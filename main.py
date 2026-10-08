"""
Git-Spectre v2 -- Async GitHub Ultra Deep-Profiler Backend
===========================================================
New in v2:
  * In-memory TTL cache (5 min)            -- prevents rate limit hammering
  * _fetch_events  -- push events for heatmap / streaks / activity hours
  * _fetch_orgs    -- organization membership
  * _fetch_gists   -- gist analytics
  * Developer Score™ (0-1000 weighted composite)
  * Contribution heatmap  (date -> commit count)
  * Activity hour grid    (7x24 matrix)
  * Streak analysis       (current / longest / total active days)
  * Tech tag cloud        (aggregated repo topics)
  * Language evolution    (per-year language breakdown)
  * Gist intelligence
  * POST /api/compare     (two users side-by-side)
  * GET  /api/rate-limit  (live rate limit status)
"""

from __future__ import annotations

import asyncio
import html as _html
import logging
import os
import re
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger("git-spectre")

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi import Path as FPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ------------------------------------------------------------
# App bootstrap
# ------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Read real client IP from X-Forwarded-For (set by Vercel / reverse proxies).
    Falls back to the socket address when the header is absent (local dev)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


# Rate limiter — keyed by real client IP (respects X-Forwarded-For behind Vercel)
limiter = Limiter(key_func=_get_client_ip)

app = FastAPI(
    title="Git-Spectre API",
    description="Ultra-premium cinematic GitHub Deep-Profiler v2",
    version="2.0.0",
    # Disable public API docs in production
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda req, exc: JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please slow down and try again shortly."},
    ),
)

# Allowed origins: production domain + localhost for dev.
# Override by setting ALLOWED_ORIGINS=https://yourdomain.com,https://other.com
# in Vercel's Environment Variables panel.
_DEFAULT_ORIGINS = [
    "https://git-spectre.vercel.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",   # in case of a future frontend dev server
]
_env_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _env_origins.split(",") if o.strip()]
    if _env_origins
    else _DEFAULT_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Attach standard security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


GITHUB_API  = "https://api.github.com"
TIMEOUT     = httpx.Timeout(28.0, connect=10.0)
MAX_RETRIES = 2
BACKOFF     = 0.5   # seconds, doubles each retry


# ------------------------------------------------------------
# In-memory response cache
# ------------------------------------------------------------

_CACHE: Dict[str, Tuple[float, Any]] = {}
CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str) -> Optional[Any]:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry[0]) < CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


# ------------------------------------------------------------
# Schemas
# ------------------------------------------------------------

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$")
# Matches all current GitHub PAT formats: ghp_, gho_, ghu_, ghr_, ghs_
_TOKEN_RE    = re.compile(r"^gh[pousr]_[A-Za-z0-9_]{36,255}$")


def _validate_username(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Username cannot be empty.")
    if not _USERNAME_RE.match(v):
        raise ValueError(
            "Invalid GitHub username. Use only letters, numbers, and hyphens (1–39 chars)."
        )
    return v


def _validate_token(v: Optional[str]) -> Optional[str]:
    """Validate GitHub PAT format — rejects obviously invalid or injected strings."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if not _TOKEN_RE.match(v):
        raise ValueError(
            "Invalid GitHub token format. Provide a valid Personal Access Token "
            "(ghp_…, gho_…, ghu_…, ghr_…, or ghs_…)."
        )
    return v


class _WithToken(BaseModel):
    """Mixin that adds a validated, optional github_token field to all request models."""

    github_token: Optional[str] = None

    @field_validator("github_token")
    @classmethod
    def validate_token(cls, v: Optional[str]) -> Optional[str]:
        return _validate_token(v)


class AnalyzeRequest(_WithToken):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return _validate_username(v)


class CompareRequest(_WithToken):
    username_a: str
    username_b: str

    @field_validator("username_a", "username_b")
    @classmethod
    def validate_usernames(cls, v: str) -> str:
        return _validate_username(v)


class BatchRequest(_WithToken):
    usernames: List[str] = Field(..., min_length=1, max_length=10)

    @field_validator("usernames", mode="before")
    @classmethod
    def validate_usernames(cls, v: List[str]) -> List[str]:
        return [_validate_username(u) for u in v]


# ------------------------------------------------------------
# HTTP helpers
# ------------------------------------------------------------

def _build_headers(token: Optional[str]) -> Dict[str, str]:
    h = {
        "Accept":               "application/vnd.github+json",
        "User-Agent":           "Git-Spectre/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


_RETRYABLE = (
    httpx.ReadError,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
)


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    **kwargs: Any,
) -> httpx.Response:
    """GET with exponential back-off retry on transient network errors."""
    delay = BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await client.get(url, **kwargs)
        except _RETRYABLE as exc:
            if attempt == MAX_RETRIES:
                logger.error("All retries exhausted for %s: %s", url, exc)
                raise HTTPException(
                    502,
                    f"Network error after {MAX_RETRIES} attempts ({type(exc).__name__}). Please retry.",
                ) from exc
            logger.warning("Attempt %d/%d failed for %s: %s. Retrying…", attempt, MAX_RETRIES, url, exc)
            await asyncio.sleep(delay)
            delay *= 2


# ------------------------------------------------------------
# Fetchers
# ------------------------------------------------------------

async def _fetch_profile(client: httpx.AsyncClient, username: str, headers: Dict) -> Dict:
    resp = await _get_with_retry(client, f"{GITHUB_API}/users/{username}", headers=headers)
    if resp.status_code == 404:
        raise HTTPException(404, f"GitHub user '{username}' not found.")
    if resp.status_code == 403:
        raise HTTPException(403, "GitHub API rate limit exceeded. Add a token via the API Vault.")
    resp.raise_for_status()
    return resp.json()


async def _fetch_repos(client: httpx.AsyncClient, username: str, headers: Dict) -> List[Dict]:
    """Fetch up to 300 repos across 3 pages concurrently."""
    async def _page(page: int) -> List[Dict]:
        resp = await _get_with_retry(
            client, f"{GITHUB_API}/users/{username}/repos",
            headers=headers,
            params={"per_page": 100, "page": page, "sort": "updated"},
        )
        if resp.status_code in (403, 404):
            return []
        resp.raise_for_status()
        return resp.json()

    pages = await asyncio.gather(_page(1), _page(2), _page(3))
    repos: List[Dict] = []
    for page in pages:
        if not page:
            break
        repos.extend(page)
        if len(page) < 100:
            break
    return repos


async def _fetch_events(client: httpx.AsyncClient, username: str, headers: Dict) -> List[Dict]:
    """Fetch up to 1000 public events (10 pages × 100) — GitHub's hard ceiling.
    This maximises full-year heatmap coverage for all activity levels."""
    async def _page(p: int) -> List[Dict]:
        resp = await _get_with_retry(
            client, f"{GITHUB_API}/users/{username}/events/public",
            headers=headers,
            params={"per_page": 100, "page": p},
        )
        if resp.status_code in (403, 404, 422):
            return []
        resp.raise_for_status()
        return resp.json()

    # Fire all 10 pages concurrently; GitHub returns [] for pages beyond history
    pages = await asyncio.gather(*[_page(p) for p in range(1, 11)])
    events: List[Dict] = []
    for page in pages:
        events.extend(page)
    return events


async def _fetch_orgs(client: httpx.AsyncClient, username: str, headers: Dict) -> List[Dict]:
    resp = await _get_with_retry(
        client, f"{GITHUB_API}/users/{username}/orgs",
        headers=headers,
        params={"per_page": 10},
    )
    if resp.status_code in (403, 404):
        return []
    resp.raise_for_status()
    return resp.json()


async def _fetch_gists(client: httpx.AsyncClient, username: str, headers: Dict) -> List[Dict]:
    resp = await _get_with_retry(
        client, f"{GITHUB_API}/users/{username}/gists",
        headers=headers,
        params={"per_page": 30},
    )
    if resp.status_code in (403, 404):
        return []
    resp.raise_for_status()
    return resp.json()


async def _fetch_followers(client: httpx.AsyncClient, username: str, headers: Dict) -> List[Dict]:
    """Fetch first 10 followers (login + avatar)."""
    resp = await _get_with_retry(
        client, f"{GITHUB_API}/users/{username}/followers",
        headers=headers,
        params={"per_page": 10},
    )
    if resp.status_code in (403, 404):
        return []
    resp.raise_for_status()
    return resp.json()


async def _fetch_following(client: httpx.AsyncClient, username: str, headers: Dict) -> List[Dict]:
    """Fetch first 10 following (login + avatar)."""
    resp = await _get_with_retry(
        client, f"{GITHUB_API}/users/{username}/following",
        headers=headers,
        params={"per_page": 10},
    )
    if resp.status_code in (403, 404):
        return []
    resp.raise_for_status()
    return resp.json()


# ------------------------------------------------------------
# Analytics — existing
# ------------------------------------------------------------

def _aggregate_languages(repos: List[Dict]) -> Dict[str, int]:
    lang_bytes: Dict[str, int] = defaultdict(int)
    for r in repos:
        if r.get("fork"):
            continue
        lang, size = r.get("language"), r.get("size", 0)
        if lang and size:
            lang_bytes[lang] += size
    return dict(sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True))


def _compute_archetype(langs: Dict, repos: List[Dict], profile: Dict) -> Dict[str, str]:
    total_bytes  = sum(langs.values()) or 1
    num_langs    = len(langs)
    followers    = profile.get("followers", 0)
    total_stars  = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    top_lang_pct = (list(langs.values())[0] / total_bytes * 100) if langs else 0

    if total_stars >= 1_000:
        return {"label": "OPEN-SOURCE LEGEND", "glow": "#f59e0b",
                "description": "Codebase that stars entire galaxies."}
    if followers >= 500:
        return {"label": "COMMUNITY BEACON", "glow": "#8b5cf6",
                "description": "A north star the dev community follows."}
    if num_langs >= 8:
        return {"label": "THE POLYGLOT", "glow": "#06b6d4",
                "description": "Fluent in more languages than most diplomats."}
    if top_lang_pct >= 80 and langs:
        top = list(langs.keys())[0]
        return {"label": f"{top.upper()} SPECIALIST", "glow": "#f97316",
                "description": f"Laser-focused mastery. 80%+ in {top}."}
    if num_langs >= 5:
        return {"label": "THE GENERALIST", "glow": "#10b981",
                "description": "A swiss-army knife of the engineering world."}
    if total_stars >= 100:
        return {"label": "RISING STAR", "glow": "#0ea5e9",
                "description": "Trajectory clearly upward. Orbital velocity reached."}
    return {"label": "CODE CRAFTSMAN", "glow": "#94a3b8",
            "description": "Building in the dark. The foundation others stand on."}


def _top_repos(repos: List[Dict], n: int = 6) -> List[Dict]:
    own = [r for r in repos if not r.get("fork")]
    top = sorted(own, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:n]
    return [
        {
            "name":        r["name"],
            "description": r.get("description") or "No description provided.",
            "stars":       r.get("stargazers_count", 0),
            "forks":       r.get("forks_count", 0),
            "open_issues": r.get("open_issues_count", 0),
            "watchers":    r.get("watchers_count", 0),
            "language":    r.get("language") or "N/A",
            "url":         r["html_url"],
            "topics":      r.get("topics", [])[:5],
            "size":        r.get("size", 0),
            "updated_at":  r.get("updated_at", "")[:10],
        }
        for r in top
    ]


# ------------------------------------------------------------
# Analytics — new v2
# ------------------------------------------------------------

def _compute_score(langs: Dict, repos: List[Dict], profile: Dict, events: List[Dict]) -> Dict[str, Any]:
    """Developer Score™: weighted composite 0–1000."""
    own_repos   = [r for r in repos if not r.get("fork")]
    total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
    followers   = profile.get("followers", 0)
    num_langs   = len(langs)
    total_repos = len(own_repos)

    # Account age in years
    created_at = profile.get("created_at", "")
    try:
        age_years = (
            datetime.now(timezone.utc)
            - datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        ).days / 365
    except Exception:
        age_years = 1.0

    # Active push days in event window
    push_dates    = {e.get("created_at", "")[:10] for e in events if e.get("type") == "PushEvent"}
    activity_days = min(len(push_dates), 90)

    scores = {
        "stars":    min(total_stars / 2000 * 300, 300),
        "followers": min(followers   / 1000 * 200, 200),
        "diversity": min(num_langs   / 12   * 150, 150),
        "repos":    min(total_repos  / 50   * 100, 100),
        "age":      min(age_years    / 8    *  80,  80),
        "activity": min(activity_days / 60  *  70,  70),
    }
    total = int(min(sum(scores.values()), 1000))

    grade_map = [(900, "S+"), (750, "S"), (600, "A"), (450, "B"), (300, "C"), (150, "D"), (0, "E")]
    grade = next(g for threshold, g in grade_map if total >= threshold)

    return {
        "total":     total,
        "breakdown": {k: int(v) for k, v in scores.items()},
        "grade":     grade,
    }


def _compute_heatmap(events: List[Dict]) -> Dict[str, int]:
    """Returns {date_str: commit_count} for all PushEvents in the event window."""
    counts: Dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("type") == "PushEvent":
            d = e.get("created_at", "")[:10]
            if d:
                n = len(e.get("payload", {}).get("commits", []))
                counts[d] += max(n, 1)
    return dict(counts)


def _compute_activity_hours(events: List[Dict]) -> List[List[int]]:
    """Returns 7×24 matrix: grid[weekday][hour] = event_count. Mon=0, Sun=6."""
    grid = [[0] * 24 for _ in range(7)]
    for e in events:
        ts = e.get("created_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            grid[dt.weekday()][dt.hour] += 1
        except Exception:
            pass
    return grid


def _compute_streaks(events: List[Dict]) -> Dict[str, int]:
    """Current streak, longest streak, total active push days from event window."""
    push_date_strs = {
        e.get("created_at", "")[:10]
        for e in events
        if e.get("type") == "PushEvent" and e.get("created_at")
    }
    if not push_date_strs:
        return {"current": 0, "longest": 0, "total_active_days": 0}

    date_set = set()
    for s in push_date_strs:
        try:
            date_set.add(date.fromisoformat(s))
        except Exception:
            pass

    if not date_set:
        return {"current": 0, "longest": 0, "total_active_days": 0}

    today = date.today()

    # Current streak: walk backwards from today (or yesterday)
    current = 0
    check = today
    while check in date_set:
        current += 1
        check -= timedelta(days=1)
    if current == 0:
        check = today - timedelta(days=1)
        while check in date_set:
            current += 1
            check -= timedelta(days=1)

    # Longest streak: iterate sorted dates
    sorted_dates = sorted(date_set)
    longest = streak = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 1

    return {"current": current, "longest": longest, "total_active_days": len(date_set)}


def _aggregate_topics(repos: List[Dict]) -> Dict[str, int]:
    """Frequency map of repo topics (own repos only), top 30."""
    counts: Dict[str, int] = defaultdict(int)
    for r in repos:
        if r.get("fork"):
            continue
        for t in r.get("topics", []):
            counts[t] += 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:30])


def _language_evolution(repos: List[Dict]) -> Dict[str, Dict[str, int]]:
    """Per-year language distribution (KB) for own repos."""
    evolution: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in repos:
        if r.get("fork"):
            continue
        lang  = r.get("language")
        size  = r.get("size", 0)
        year  = r.get("created_at", "")[:4]
        if lang and size and year.isdigit():
            evolution[year][lang] += size
    return {
        y: dict(sorted(v.items(), key=lambda kv: kv[1], reverse=True)[:6])
        for y, v in sorted(evolution.items())
    }


def _gist_stats(gists: List[Dict]) -> Dict[str, Any]:
    if not gists:
        return {"total": 0, "most_forked": None, "top_language": None, "total_comments": 0}

    total_comments = sum(g.get("comments", 0) for g in gists)

    most_forked = max(gists, key=lambda g: len(g.get("forks", [])), default=None)

    lang_counts: Dict[str, int] = defaultdict(int)
    for g in gists:
        for _, fdata in g.get("files", {}).items():
            lang = fdata.get("language")
            if lang:
                lang_counts[lang] += 1

    return {
        "total":          len(gists),
        "total_comments": total_comments,
        "top_language":   max(lang_counts, key=lang_counts.get) if lang_counts else None,
        "most_forked": {
            "description": most_forked.get("description") or "Untitled Gist",
            "url":         most_forked.get("html_url", ""),
            "forks":       len(most_forked.get("forks", [])),
        } if most_forked else None,
    }


def _extract_commit_messages(events: List[Dict]) -> List[str]:
    """First lines of commit messages from PushEvents (up to 200 total)."""
    messages: List[str] = []
    for e in events:
        if e.get("type") == "PushEvent":
            for commit in e.get("payload", {}).get("commits", []):
                msg = commit.get("message", "").strip()
                if msg:
                    messages.append(msg.split("\n")[0][:200])
    return messages[:200]


def _compute_community(events: List[Dict], username: str) -> Dict[str, Any]:
    """PR/issue/comment activity and external repository contributions."""
    prs_opened    = 0
    prs_merged    = 0
    issues_opened = 0
    issue_comments = 0
    external_repos: Dict[str, str] = {}

    for e in events:
        etype    = e.get("type", "")
        repo_name = e.get("repo", {}).get("name", "")
        payload  = e.get("payload", {})

        if etype == "PullRequestEvent":
            action = payload.get("action", "")
            if action == "opened":
                prs_opened += 1
            elif action == "closed" and payload.get("pull_request", {}).get("merged"):
                prs_merged += 1
        elif etype == "IssuesEvent" and payload.get("action") == "opened":
            issues_opened += 1
        elif etype == "IssueCommentEvent":
            issue_comments += 1

        if etype == "PushEvent" and not repo_name.lower().startswith(f"{username.lower()}/"):
            if repo_name and repo_name not in external_repos:
                external_repos[repo_name] = f"https://github.com/{repo_name}"

    return {
        "prs_opened":     prs_opened,
        "prs_merged":     prs_merged,
        "issues_opened":  issues_opened,
        "issue_comments": issue_comments,
        "external_repos": [
            {"name": n, "url": u} for n, u in list(external_repos.items())[:8]
        ],
    }


def _compute_fork_details(repos: List[Dict]) -> List[Dict]:
    """Top forked repos sorted by stars."""
    forks = [r for r in repos if r.get("fork")]
    return [
        {
            "name":     r["name"],
            "url":      r["html_url"],
            "stars":    r.get("stargazers_count", 0),
            "language": r.get("language") or "N/A",
            "updated":  r.get("updated_at", "")[:10],
        }
        for r in sorted(forks, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:8]
    ]


def _compute_lang_repo_counts(repos: List[Dict]) -> Dict[str, int]:
    """Number of own (non-forked) repos per language."""
    counts: Dict[str, int] = defaultdict(int)
    for r in repos:
        if r.get("fork"):
            continue
        lang = r.get("language")
        if lang:
            counts[lang] += 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def _compute_peak_hour(events: List[Dict]) -> Dict[str, Any]:
    """Peak coding hour + weekday persona derived from public events."""
    hour_counts = [0] * 24
    day_counts  = [0] * 7
    for e in events:
        ts = e.get("created_at", "")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            hour_counts[dt.hour] += 1
            day_counts[dt.weekday()] += 1
        except Exception:
            pass
    if not any(hour_counts):
        return {"hour": "—", "day": "—", "persona": "Ghost Coder", "is_night_owl": False}
    peak_h = hour_counts.index(max(hour_counts))
    peak_d = day_counts.index(max(day_counts))
    days   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if peak_h == 0:      h_label = "12 AM"
    elif peak_h < 12:    h_label = f"{peak_h} AM"
    elif peak_h == 12:   h_label = "12 PM"
    else:                h_label = f"{peak_h - 12} PM"
    night = peak_h >= 22 or peak_h <= 4
    if night:                  persona = "🌙 Night Owl"
    elif 5 <= peak_h <= 8:     persona = "🌅 Early Bird"
    elif 9 <= peak_h <= 17:    persona = "☀️ 9-to-5 Dev"
    else:                      persona = "🌆 Evening Coder"
    return {"hour": h_label, "day": days[peak_d], "persona": persona, "is_night_owl": night}


def _compute_star_velocity(repos: List[Dict], profile: Dict) -> float:
    """Stars earned per year of account existence (own repos only)."""
    own_repos   = [r for r in repos if not r.get("fork")]
    total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
    try:
        age_years = max(
            (datetime.now(timezone.utc)
             - datetime.fromisoformat(profile.get("created_at", "").replace("Z", "+00:00"))).days / 365,
            0.1,
        )
    except Exception:
        age_years = 1.0
    return round(total_stars / age_years, 1)


def _compute_roast(langs: Dict, repos: List[Dict], profile: Dict,
                   events: List[Dict], streaks: Dict) -> str:
    """Data-grounded humorous developer roast (max 2 sentences)."""
    own       = [r for r in repos if not r.get("fork")]
    stars     = sum(r.get("stargazers_count", 0) for r in own)
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    forks_cnt = len([r for r in repos if r.get("fork")])
    no_desc   = sum(1 for r in own if not r.get("description"))
    streak    = streaks.get("current", 0)
    n         = len(own) or 1
    lines: List[str] = []
    if no_desc / n > 0.7:
        lines.append("Most repos have no description — mystery wrapped in a .gitignore.")
    if forks_cnt > n * 1.5 and forks_cnt > 3:
        lines.append(f"Forked {forks_cnt} repos, created {n}. Collector energy, not creator energy.")
    if streak == 0:
        lines.append("Commit streak: 0. The GitHub grass is growing back.")
    elif streak < 3:
        lines.append(f"A {streak}-day streak. Barely keeping the garden alive.")
    if following and followers and following > followers * 3:
        lines.append(f"Following {following}, only {followers} follow back. Unrequited code love.")
    if len(langs) == 1 and langs:
        lines.append(f"Only {list(langs.keys())[0]}. Loyalty is admirable. Tunnel vision, less so.")
    elif len(langs) > 12:
        lines.append(f"Codes in {len(langs)} languages — polyglot or commitment issues?")
    if stars == 0:
        lines.append("Zero stars. Not even from a rubber duck.")
    elif stars < 5:
        lines.append(f"Only {stars} star{'s' if stars > 1 else ''}. Keep shipping.")
    if not lines:
        lines.append("Suspiciously well-rounded. Either a 10× engineer or very good at hiding skeletons.")
    return " ".join(lines[:2])


def _compute_readme_quality(readme: Dict[str, Any]) -> Dict[str, Any]:
    """Score the user's profile README 0–100 across 6 signals."""
    if not readme.get("found") or not readme.get("content"):
        return {"found": False, "score": 0, "signals": {}}

    content: str = readme["content"]
    lower = content.lower()
    length = len(content)

    signals: Dict[str, bool] = {
        "has_badges":     bool(re.search(r"!\[.*?\]\(https?://.*?(badge|shield|img\.shields).*?\)", lower)),
        "has_gif_or_img": bool(re.search(r"!\[.*?\]\(https?://.*?\.(gif|png|jpg|svg|webp)", lower)),
        "has_links":      bool(re.search(r"\[.+?\]\(https?://", content)),
        "is_long":        length >= 300,
        "has_headers":    bool(re.search(r"^#{1,3} ", content, re.MULTILINE)),
        "has_code_block": bool(re.search(r"```|`[^`]+`", content)),
    }

    weights = {"has_badges": 18, "has_gif_or_img": 18, "has_links": 16,
               "is_long": 18, "has_headers": 16, "has_code_block": 14}
    score = int(sum(weights[k] for k, v in signals.items() if v))
    return {"found": True, "score": score, "signals": signals, "html_url": readme.get("html_url", "")}


def _compute_wrapped(repos: List[Dict], events: List[Dict],
                     profile: Dict, streaks: Dict,
                     langs: Dict, heatmap: Dict) -> Dict[str, Any]:
    """GitHub Wrapped: year-in-review highlights derived from existing data."""
    import calendar as _cal

    now = datetime.now(timezone.utc)
    current_year = str(now.year)

    # Total commits this year (from heatmap keys)
    year_commits = sum(v for k, v in heatmap.items() if k.startswith(current_year))

    # Best day (most commits)
    best_day = max(heatmap.items(), key=lambda kv: kv[1]) if heatmap else ("—", 0)

    # Best month by commit count
    month_counts: Dict[str, int] = defaultdict(int)
    for ds, cnt in heatmap.items():
        if ds.startswith(current_year):
            month_counts[ds[:7]] += cnt
    best_month_key = max(month_counts, key=month_counts.get) if month_counts else None
    if best_month_key:
        mo = int(best_month_key.split("-")[1])
        best_month = f"{_cal.month_abbr[mo]} {current_year}"
        best_month_commits = month_counts[best_month_key]
    else:
        best_month, best_month_commits = "—", 0

    # Top language
    top_language = list(langs.keys())[0] if langs else "—"

    # Biggest repo (by stars, own only)
    own = [r for r in repos if not r.get("fork")]
    biggest = max(own, key=lambda r: r.get("stargazers_count", 0), default=None)

    # Event type breakdown
    event_types: Dict[str, int] = defaultdict(int)
    for e in events:
        event_types[e.get("type", "Other")] += 1
    top_event = max(event_types, key=event_types.get) if event_types else "—"

    # PR merge rate
    prs_opened = sum(1 for e in events if e.get("type") == "PullRequestEvent"
                     and e.get("payload", {}).get("action") == "opened")
    prs_merged = sum(1 for e in events if e.get("type") == "PullRequestEvent"
                     and e.get("payload", {}).get("action") == "closed"
                     and e.get("payload", {}).get("pull_request", {}).get("merged"))
    merge_rate = round(prs_merged / prs_opened * 100) if prs_opened else None

    # New repos created this year
    new_repos_year = sum(1 for r in own if r.get("created_at", "").startswith(current_year))

    # Account age label
    try:
        age_years = (now - datetime.fromisoformat(
            profile.get("created_at", "").replace("Z", "+00:00")
        )).days / 365
        age_label = f"{age_years:.1f} years on GitHub"
    except Exception:
        age_label = "—"

    return {
        "year":              current_year,
        "year_commits":      year_commits,
        "best_day":          {"date": best_day[0], "commits": best_day[1]},
        "best_month":        {"label": best_month, "commits": best_month_commits},
        "top_language":      top_language,
        "biggest_repo":      {
            "name":  biggest["name"] if biggest else "—",
            "stars": biggest.get("stargazers_count", 0) if biggest else 0,
            "url":   biggest["html_url"] if biggest else "#",
        } if biggest else None,
        "top_event_type":    top_event,
        "prs_opened":        prs_opened,
        "prs_merged":        prs_merged,
        "pr_merge_rate":     merge_rate,
        "longest_streak":    streaks.get("longest", 0),
        "current_streak":    streaks.get("current", 0),
        "new_repos_year":    new_repos_year,
        "total_stars":       sum(r.get("stargazers_count", 0) for r in own),
        "total_followers":   profile.get("followers", 0),
        "age_label":         age_label,
    }


def _compute_social_graph(followers_raw: List[Dict], following_raw: List[Dict]) -> Dict[str, Any]:
    """Mutual follows, fans, and one-sided following from fetched lists."""
    fl = {f["login"].lower() for f in followers_raw}
    fw = {f["login"].lower() for f in following_raw}
    mutual   = fl & fw
    fans     = fl - fw
    one_way  = fw - fl

    def _fmt(src: List[Dict], s: set) -> List[Dict]:
        return [
            {"login": f["login"],
             "avatar_url": f.get("avatar_url", ""),
             "url": f.get("html_url", f"https://github.com/{f['login']}")}
            for f in src if f["login"].lower() in s
        ][:5]

    return {
        "mutual_count":         len(mutual),
        "fans_count":           len(fans),
        "following_only_count": len(one_way),
        "mutual":               _fmt(followers_raw, mutual),
        "fans":                 _fmt(followers_raw, fans),
        "following_only":       _fmt(following_raw, one_way),
    }


async def _fetch_contribution_calendar(
    client: httpx.AsyncClient, username: str
) -> Dict[str, int]:
    """
    Scrape GitHub's public contribution calendar SVG.
    URL: https://github.com/users/{username}/contributions
    Returns {date_str: approx_count} derived from contribution level (0-4).
    Level → approximate commit count mapping: 1→1, 2→3, 3→6, 4→12.
    Covers the full visible year with no authentication required.
    """
    import re as _re
    LEVEL_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 12}
    try:
        resp = await client.get(
            f"https://github.com/users/{username}/contributions",
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "Mozilla/5.0 (compatible; Git-Spectre/2.2)",
            },
            follow_redirects=True,
            timeout=httpx.Timeout(15.0),
        )
        if resp.status_code != 200:
            return {}
        html = resp.text
        counts: Dict[str, int] = {}
        # GitHub renders cells like:
        #   data-date="2026-09-19" ... data-level="2"
        # Attribute order may vary; try both orderings.
        for m in _re.finditer(
            r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"', html
        ):
            lvl = int(m.group(2))
            if lvl > 0:
                counts[m.group(1)] = LEVEL_COUNT.get(lvl, lvl)
        if not counts:
            for m in _re.finditer(
                r'data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"', html
            ):
                lvl = int(m.group(1))
                if lvl > 0:
                    counts[m.group(2)] = LEVEL_COUNT.get(lvl, lvl)
        return counts
    except Exception as exc:
        logger.warning("Contribution calendar scrape failed for '%s': %s", username, exc)
        return {}


# ------------------------------------------------------------
# Core analysis (shared by /analyze and /compare)
# ------------------------------------------------------------


async def _run_analysis(username: str, token: Optional[str]) -> Dict[str, Any]:
    """Full profile analysis. Checks TTL cache first."""
    cache_key = f"{username.lower()}:{bool(token)}"
    cached    = _cache_get(cache_key)
    if cached:
        return {**cached, "cached": True}

    headers = _build_headers(token)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            (
                profile, repos, events, orgs, gists, followers_raw, following_raw,
                cal_heatmap,
            ) = await asyncio.gather(
                _fetch_profile(client, username, headers),
                _fetch_repos(client, username, headers),
                _fetch_events(client, username, headers),
                _fetch_orgs(client, username, headers),
                _fetch_gists(client, username, headers),
                _fetch_followers(client, username, headers),
                _fetch_following(client, username, headers),
                _fetch_contribution_calendar(client, username),
            )
        except HTTPException:
            raise
        except httpx.HTTPStatusError as exc:
            raise HTTPException(exc.response.status_code, f"GitHub returned {exc.response.status_code}.")
        except Exception as exc:
            logger.exception("Unexpected error for '%s'", username)
            raise HTTPException(502, f"Unexpected error: {exc}")

    lang_bytes   = _aggregate_languages(repos)
    total_stars  = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    streaks_data = _compute_streaks(events)

    result: Dict[str, Any] = {
        "cached": False,
        "profile": {
            "login":        profile.get("login"),
            "name":         profile.get("name") or profile.get("login"),
            "bio":          profile.get("bio") or "No bio provided.",
            "avatar_url":   profile.get("avatar_url"),
            "html_url":     profile.get("html_url"),
            "location":     profile.get("location") or "Unknown",
            "company":      profile.get("company") or "Independent",
            "blog":         profile.get("blog") or "",
            "twitter":      profile.get("twitter_username") or "",
            "created_at":   profile.get("created_at", "")[:4],
            "followers":    profile.get("followers", 0),
            "following":    profile.get("following", 0),
            "public_repos": profile.get("public_repos", 0),
        },
        "stats": {
            "total_stars":  total_stars,
            "total_repos":  len(repos),
            "own_repos":    len([r for r in repos if not r.get("fork")]),
            "forked_repos": len([r for r in repos if r.get("fork")]),
        },
        "languages":     dict(list(lang_bytes.items())[:8]),
        "archetype":     _compute_archetype(lang_bytes, repos, profile),
        "top_repos":     _top_repos(repos, n=6),
        "score":         _compute_score(lang_bytes, repos, profile, events),
        # Heatmap: calendar scrape (full year, level-based) merged with events data
        # (exact commit counts for recent dates override the level approximation)
        "heatmap":       {**cal_heatmap, **_compute_heatmap(events)},
        "activity_hours": _compute_activity_hours(events),
        "streaks":       streaks_data,
        "topics":        _aggregate_topics(repos),
        "lang_evolution": _language_evolution(repos),
        "gists":          _gist_stats(gists),
        "commit_messages": _extract_commit_messages(events),
        "community":      _compute_community(events, username),
        "fork_details":   _compute_fork_details(repos),
        "lang_repo_counts": _compute_lang_repo_counts(repos),
        "peak_hour":        _compute_peak_hour(events),
        "star_velocity":    _compute_star_velocity(repos, profile),
        "roast":            _compute_roast(lang_bytes, repos, profile, events, streaks_data),
        "social_graph":     _compute_social_graph(followers_raw, following_raw),
        "pr_merge_rate":    (
            lambda opened, merged: round(merged / opened * 100) if opened else None
        )(
            sum(1 for e in events if e.get("type") == "PullRequestEvent" and e.get("payload", {}).get("action") == "opened"),
            sum(1 for e in events if e.get("type") == "PullRequestEvent" and e.get("payload", {}).get("action") == "closed" and e.get("payload", {}).get("pull_request", {}).get("merged")),
        ),
        "orgs": [
            {
                "login":      o["login"],
                "avatar_url": o.get("avatar_url", ""),
                "url":        f"https://github.com/{o['login']}",
            }
            for o in orgs[:8]
        ],
        "followers_list": [
            {
                "login":      f["login"],
                "avatar_url": f.get("avatar_url", ""),
                "url":        f.get("html_url", f"https://github.com/{f['login']}"),
            }
            for f in followers_raw[:10]
        ],
        "following_list": [
            {
                "login":      f["login"],
                "avatar_url": f.get("avatar_url", ""),
                "url":        f.get("html_url", f"https://github.com/{f['login']}"),
            }
            for f in following_raw[:10]
        ],
    }

    # README quality — fetch separately (not parallel to avoid extra API hit on cache hits)
    readme_raw = await _fetch_readme_for_quality(username, headers)
    result["readme_quality"] = _compute_readme_quality(readme_raw)

    # GitHub Wrapped
    result["wrapped"] = _compute_wrapped(
        repos, events, profile, streaks_data,
        lang_bytes, result["heatmap"],
    )

    _cache_set(cache_key, result)
    return result


async def _fetch_readme_for_quality(username: str, headers: Dict) -> Dict[str, Any]:
    """Lightweight README fetch for quality scoring — reuses the readme endpoint logic."""
    import base64 as _b64
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{username}/{username}/readme",
            headers=headers,
        )
        if resp.status_code in (404, 403, 422):
            return {"found": False, "content": "", "html_url": ""}
        try:
            resp.raise_for_status()
        except Exception:
            return {"found": False, "content": "", "html_url": ""}
        data = resp.json()
        try:
            content = _b64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
        except Exception:
            content = ""
        return {"found": bool(content.strip()), "content": content, "html_url": data.get("html_url", "")}


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def serve_spa() -> FileResponse:
    return FileResponse(str(BASE_DIR / "index.html"))


@limiter.limit("15/minute")
@app.post("/api/analyze")
async def analyze(request: Request, payload: AnalyzeRequest) -> Dict[str, Any]:
    token = payload.github_token or os.getenv("GITHUB_TOKEN")
    return await _run_analysis(payload.username, token)


@limiter.limit("8/minute")
@app.post("/api/compare")
async def compare(request: Request, payload: CompareRequest) -> Dict[str, Any]:
    token = payload.github_token or os.getenv("GITHUB_TOKEN")
    try:
        result_a, result_b = await asyncio.gather(
            _run_analysis(payload.username_a, token),
            _run_analysis(payload.username_b, token),
        )
    except HTTPException:
        raise
    return {"user_a": result_a, "user_b": result_b}


@limiter.limit("4/minute")
@app.post("/api/batch")
async def batch_analyze(request: Request, payload: BatchRequest) -> List[Dict[str, Any]]:
    """Analyze up to 10 profiles concurrently and return a sorted leaderboard."""
    usernames = payload.usernames  # already validated & stripped by Pydantic
    if not usernames:
        raise HTTPException(422, "At least one username required.")
    token = payload.github_token or os.getenv("GITHUB_TOKEN")
    results = await asyncio.gather(
        *[_run_analysis(u, token) for u in usernames],
        return_exceptions=True,
    )
    out: List[Dict[str, Any]] = []
    for uname, res in zip(usernames, results):
        if isinstance(res, Exception):
            out.append({"username": uname, "error": str(res), "score": -1})
        else:
            out.append({
                "username":       uname,
                "avatar_url":     res["profile"]["avatar_url"],
                "name":           res["profile"]["name"],
                "score":          res["score"]["total"],
                "grade":          res["score"]["grade"],
                "archetype":      res["archetype"]["label"],
                "archetype_glow": res["archetype"]["glow"],
                "top_language":   next(iter(res["languages"]), "N/A"),
                "total_stars":    res["stats"]["total_stars"],
                "followers":      res["profile"]["followers"],
                "repos":          res["stats"]["own_repos"],
                "streak":         res["streaks"]["current"],
                "html_url":       res["profile"]["html_url"],
            })
    return sorted(out, key=lambda x: x.get("score", -1), reverse=True)


@app.get("/embed/{username}", include_in_schema=False)
async def embed_profile(
    username: str = FPath(
        ...,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
        description="GitHub username (1\u201339 chars, alphanumeric and hyphens)",
    ),
) -> HTMLResponse:
    """Minimal embeddable profile card for portfolios and READMEs."""
    token = os.getenv("GITHUB_TOKEN")
    try:
        data = await _run_analysis(username.strip(), token)
    except HTTPException as exc:
        return HTMLResponse(
            f"<p style='font-family:monospace;color:#ef4444;padding:16px'>Error: {_html.escape(str(exc.detail))}</p>",
            status_code=exc.status_code,
        )

    p   = data["profile"]
    sc  = data["score"]
    arc = data["archetype"]
    langs = list(data["languages"].items())[:4]
    tot   = sum(v for _, v in langs) or 1
    grade_colors = {
        "S+": "#f59e0b", "S": "#10b981", "A": "#06b6d4",
        "B":  "#8b5cf6", "C": "#f97316", "D": "#ef4444", "E": "#6b7280",
    }
    sc_col = grade_colors.get(sc["grade"], "#22d3ee")

    # Escape all GitHub-sourced strings before injecting into HTML
    p_name    = _html.escape(str(p.get("name") or p.get("login", "")))
    p_login   = _html.escape(str(p.get("login", "")))
    p_avatar  = _html.escape(str(p.get("avatar_url", "")))
    arc_label = _html.escape(str(arc.get("label", "")))
    arc_glow  = _html.escape(str(arc.get("glow", "#22d3ee")))
    sc_total  = int(sc.get("total", 0))       # always int, safe to interpolate directly
    sc_grade  = _html.escape(str(sc.get("grade", "E")))
    sc_col_e  = _html.escape(sc_col)

    lang_html = "".join(
        f'<div style="margin-bottom:6px">'
        f'<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;'
        f'font-family:monospace;color:#a1a1aa"><span>{_html.escape(str(lg))}</span><span>{round(v/tot*100)}%</span></div>'
        f'<div style="background:rgba(255,255,255,0.08);border-radius:3px;height:3px">'
        f'<div style="width:{round(v/tot*100)}%;background:#22d3ee;border-radius:3px;height:3px">'
        f'</div></div></div>'
        for lg, v in langs
    )
    card_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Inter',sans-serif;background:#09090b;color:#e4e4e7;padding:20px;border-radius:12px;border:1px solid rgba(34,211,238,.15)}}</style>
</head><body>
<div style="display:flex;align-items:center;gap:14px;margin-bottom:16px">
  <img src="{p_avatar}" style="width:56px;height:56px;border-radius:12px;border:2px solid rgba(34,211,238,.3)">
  <div style="flex:1;min-width:0">
    <div style="font-weight:900;font-size:17px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{p_name}</div>
    <div style="color:#22d3ee;font-family:'JetBrains Mono',monospace;font-size:12px">@{p_login}</div>
    <span style="background:{arc_glow}22;border:1px solid {arc_glow}55;color:{arc_glow};
      font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;
      padding:2px 8px;border-radius:20px;margin-top:4px;display:inline-block">{arc_label}</span>
  </div>
  <div style="text-align:center;flex-shrink:0">
    <div style="font-size:26px;font-weight:900;color:{sc_col_e}">{sc_total}</div>
    <div style="font-size:9px;color:#52525b;font-family:'JetBrains Mono',monospace">/1000</div>
    <div style="font-size:14px;font-weight:900;color:{sc_col_e}">{sc_grade}</div>
  </div>
</div>
{lang_html}
<div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,.06);
  text-align:center;font-size:9px;color:#3f3f46;font-family:'JetBrains Mono',monospace;letter-spacing:.1em">
  <a href="https://git-spectre.vercel.app/?u={p_login}" target="_blank"
     style="color:#22d3ee44;text-decoration:none">GIT-SPECTRE</a>
</div>
</body></html>"""
    return HTMLResponse(card_html)


@app.get("/api/rate-limit")
async def rate_limit_endpoint() -> Dict[str, Any]:
    headers = _build_headers(os.getenv("GITHUB_TOKEN"))
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await _get_with_retry(client, f"{GITHUB_API}/rate_limit", headers=headers)
        resp.raise_for_status()
        data = resp.json()
    core = data.get("resources", {}).get("core", {})
    return {
        "limit":     core.get("limit", 60),
        "remaining": core.get("remaining", 0),
        "reset":     core.get("reset", 0),
        "used":      core.get("used", 0),
    }


@app.get("/api/readme/{username}")
async def get_readme(
    username: str = FPath(
        ...,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
        description="GitHub username",
    ),
) -> Dict[str, Any]:
    """Fetch the user's profile README from their username/username repo."""
    import base64 as _b64
    token   = os.getenv("GITHUB_TOKEN")
    headers = _build_headers(token)
    async with httpx.AsyncClient(timeout=httpx.Timeout(12.0)) as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{username}/{username}/readme",
            headers=headers,
        )
        if resp.status_code in (404, 403, 422):
            return {"found": False, "content": "", "html_url": ""}
        try:
            resp.raise_for_status()
        except Exception:
            return {"found": False, "content": "", "html_url": ""}
        data = resp.json()
        try:
            content = _b64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
        except Exception:
            content = ""
        return {
            "found":    bool(content.strip()),
            "content":  content,
            "html_url": data.get("html_url", ""),
        }


@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, str]:
    """Liveness probe for uptime monitors."""
    return {"status": "ok", "version": "2.2"}


# ------------------------------------------------------------
# Dev entry-point
# ------------------------------------------------------------

@app.get("/api/badge/{username}", include_in_schema=False)
async def badge_svg(
    username: str = FPath(
        ...,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
        description="GitHub username",
    ),
) -> Response:
    """Return a dynamic shields.io-style SVG badge: Dev Score + Grade."""
    token = os.getenv("GITHUB_TOKEN")
    try:
        data = await _run_analysis(username.strip(), token)
    except HTTPException:
        # Return a fallback "not found" badge
        svg = _make_badge_svg("Git-Spectre", "not found", "#6b7280")
        return Response(svg, media_type="image/svg+xml",
                        headers={"Cache-Control": "no-cache"})

    sc  = data["score"]
    arc = data["archetype"]
    grade_colors = {
        "S+": "#f59e0b", "S": "#10b981", "A": "#06b6d4",
        "B":  "#8b5cf6", "C": "#f97316", "D": "#ef4444", "E": "#6b7280",
    }
    color = grade_colors.get(sc["grade"], "#22d3ee")
    label = f"Score {sc['total']} · {sc['grade']}"
    svg = _make_badge_svg("Git-Spectre", label, color)
    return Response(
        svg, media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=600"},
    )


def _make_badge_svg(left: str, right: str, color: str) -> str:
    """Minimal shields.io-compatible flat SVG badge."""
    # Escape all values injected into SVG/XML content or attributes
    left_e  = _html.escape(left,  quote=True)
    right_e = _html.escape(right, quote=True)
    color_e = _html.escape(color, quote=True)
    # Approximate text widths (monospace heuristic)
    lw = len(left) * 6 + 10
    rw = len(right) * 6 + 10
    total = lw + rw
    lx = lw // 2
    rx = lw + rw // 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{total}" height="20" role="img" aria-label="{left_e}: {right_e}">
  <title>{left_e}: {right_e}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{lw}" height="20" fill="#555"/>
    <rect x="{lw}" width="{rw}" height="20" fill="{color_e}"/>
    <rect width="{total}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="110" text-rendering="geometricPrecision">
    <text x="{lx * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(lw - 10) * 10}" lengthAdjust="spacing">{left_e}</text>
    <text x="{lx * 10}" y="140" transform="scale(.1)" textLength="{(lw - 10) * 10}" lengthAdjust="spacing">{left_e}</text>
    <text x="{rx * 10}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="{(rw - 10) * 10}" lengthAdjust="spacing">{right_e}</text>
    <text x="{rx * 10}" y="140" transform="scale(.1)" textLength="{(rw - 10) * 10}" lengthAdjust="spacing">{right_e}</text>
  </g>
</svg>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)