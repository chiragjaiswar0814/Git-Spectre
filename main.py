"""
Git-Spectre -- Async GitHub Deep-Profiler Backend
==================================================
Principal Developer Tools Architect Pattern
  * Pure httpx + asyncio  (no PyGithub)
  * asyncio.gather()      for concurrent API calls
  * FastAPI               as the ASGI framework
  * Uvicorn               as the production server
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("git-spectre")

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ------------------------------------------------------------
# App bootstrap
# ------------------------------------------------------------

app = FastAPI(
    title="Git-Spectre API",
    description="Ultra-premium cinematic GitHub Deep-Profiler",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_API  = "https://api.github.com"
TIMEOUT     = httpx.Timeout(30.0, connect=15.0)
MAX_RETRIES = 3
BACKOFF     = 1.0  # seconds; doubles each retry


# ------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    username: str
    github_token: Optional[str] = None


# ------------------------------------------------------------
# Async fetchers  (raw REST, zero wrapper libraries)
# ------------------------------------------------------------

def _build_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {
        "Accept":               "application/vnd.github+json",
        "User-Agent":           "Git-Spectre/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# Transient network errors that are safe to retry
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
                logger.error("All %d retries exhausted for %s: %s", MAX_RETRIES, url, exc)
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"Network error communicating with GitHub after {MAX_RETRIES} attempts. "
                        f"This is usually a transient issue — please try again. ({type(exc).__name__})"
                    ),
                ) from exc
            logger.warning(
                "Attempt %d/%d failed for %s (%s). Retrying in %.1fs…",
                attempt, MAX_RETRIES, url, exc, delay,
            )
            await asyncio.sleep(delay)
            delay *= 2


async def _fetch_profile(
    client: httpx.AsyncClient,
    username: str,
    headers: Dict[str, str],
) -> Dict[str, Any]:
    resp = await _get_with_retry(client, f"{GITHUB_API}/users/{username}", headers=headers)
    if resp.status_code == 404:
        raise HTTPException(404, detail=f"GitHub user '{username}' not found.")
    if resp.status_code == 403:
        raise HTTPException(403, detail="GitHub API rate limit exceeded. Add a token via the API Vault.")
    resp.raise_for_status()
    return resp.json()


async def _fetch_repos(
    client: httpx.AsyncClient,
    username: str,
    headers: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Fetch up to 300 repos across 3 pages concurrently."""

    async def _page(page: int) -> List[Dict[str, Any]]:
        resp = await _get_with_retry(
            client,
            f"{GITHUB_API}/users/{username}/repos",
            headers=headers,
            params={"per_page": 100, "page": page, "sort": "updated"},
        )
        if resp.status_code in (403, 404):
            return []
        resp.raise_for_status()
        return resp.json()

    pages = await asyncio.gather(_page(1), _page(2), _page(3))
    repos: List[Dict[str, Any]] = []
    for page in pages:
        if not page:
            break
        repos.extend(page)
        if len(page) < 100:
            break
    return repos


# ------------------------------------------------------------
# Analytics Engine
# ------------------------------------------------------------

def _aggregate_languages(repos: List[Dict[str, Any]]) -> Dict[str, int]:
    lang_bytes: Dict[str, int] = defaultdict(int)
    for repo in repos:
        if repo.get("fork"):
            continue
        lang = repo.get("language")
        size = repo.get("size", 0)
        if lang and size:
            lang_bytes[lang] += size
    return dict(sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True))


def _compute_archetype(
    langs: Dict[str, int],
    repos: List[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Dict[str, str]:
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


def _top_repos(repos: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
    own = [r for r in repos if not r.get("fork")]
    top = sorted(own, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:n]
    return [
        {
            "name":        r["name"],
            "description": r.get("description") or "No description provided.",
            "stars":       r.get("stargazers_count", 0),
            "forks":       r.get("forks_count", 0),
            "language":    r.get("language") or "N/A",
            "url":         r["html_url"],
            "topics":      r.get("topics", [])[:4],
        }
        for r in top
    ]


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def serve_spa() -> FileResponse:
    return FileResponse("index.html")


@app.post("/api/analyze")
async def analyze(payload: AnalyzeRequest) -> Dict[str, Any]:
    username = payload.username.strip()
    token    = payload.github_token or os.getenv("GITHUB_TOKEN")

    if not username:
        raise HTTPException(status_code=422, detail="Username cannot be empty.")

    headers = _build_headers(token)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # ---- The Concurrency Magic -------------------------------------------
            profile, repos = await asyncio.gather(
                _fetch_profile(client, username, headers),
                _fetch_repos(client, username, headers),
            )
            # -------------------------------------------------------------------------
    except HTTPException:
        raise  # already shaped correctly, let FastAPI handle it
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code,
                            detail=f"GitHub returned {exc.response.status_code}.")
    except Exception as exc:
        logger.exception("Unexpected error during scan of '%s'", username)
        raise HTTPException(status_code=502,
                            detail=f"Unexpected network error: {exc}")

    lang_bytes  = _aggregate_languages(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    archetype   = _compute_archetype(lang_bytes, repos, profile)
    top_repos   = _top_repos(repos)
    lang_chart  = dict(list(lang_bytes.items())[:8])

    return {
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
        "languages": lang_chart,
        "archetype": archetype,
        "top_repos": top_repos,
    }


# ------------------------------------------------------------
# Dev entry-point
# ------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)