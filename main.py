"""
Git-Spectre Backend
===================
FastAPI entry point, security middleware, rate limiting, and route definitions.
Core business logic, analytics, and scrapers are decomposed into the `core/` package.
"""

from __future__ import annotations

import asyncio
import html as _html
from typing import Any, Dict, List, Optional

import base64
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi import Path as FPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.cache import _cache_get, _cache_set
from core.analytics import (
    _aggregate_languages,
    _compute_archetype,
    _compute_score,
    _compute_streaks,
)
from core.config import (
    ALLOWED_ORIGINS,
    APP_VERSION,
    APP_VERSION_MAJOR,
    APP_VERSION_SHORT,
    BASE_DIR,
    GITHUB_API,
    GITHUB_REPO,
    GITHUB_REPO_URL,
    _get_server_token,
    logger,
)
from core.fetchers import _build_headers, _get_with_retry
from core.schemas import (
    AnalyzeRequest,
    BatchRequest,
    CompareRequest,
    _make_badge_svg,
    _validate_token,
    _validate_username,
)
from core.badge import (
    GRADE_COLORS,
    generate_dossier_card,
    generate_not_found_badge,
    generate_pill_badge,
    generate_profile_badge,
)
from core.service import _run_analysis
from core.leaderboard import (
    get_cached_profile_record,
    get_leaderboard,
    get_leaderboard_languages,
    get_profile_rank,
)

# Re-export key functions for backwards compatibility with tests and tooling
__all__ = [
    "app",
    "APP_VERSION",
    "APP_VERSION_SHORT",
    "APP_VERSION_MAJOR",
    "GITHUB_REPO",
    "GITHUB_REPO_URL",
    "_validate_username",
    "_validate_token",
    "_compute_archetype",
    "_compute_score",
    "_compute_streaks",
    "_aggregate_languages",
    "_run_analysis",
    "_get_server_token",
    "get_leaderboard",
    "get_profile_rank",
]


# ------------------------------------------------------------
# App bootstrap & Rate Limiting
# ------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Read real client IP from X-Forwarded-For (set by Vercel / reverse proxies).
    Falls back to the socket address when the header is absent (local dev)."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_client_ip)

app = FastAPI(
    title="Git-Spectre API",
    description=f"Ultra-premium cinematic GitHub Deep-Profiler {APP_VERSION_MAJOR}",
    version=APP_VERSION,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
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


# Mount static assets directory
_static_dir = BASE_DIR / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def serve_spa() -> HTMLResponse:
    """Serve the single-page application entry point with version dynamically injected."""
    raw = (BASE_DIR / "index.html").read_text(encoding="utf-8")
    content = (
        raw
        .replace("{{APP_VERSION_SHORT}}", APP_VERSION_SHORT)
        .replace("{{APP_VERSION_MAJOR}}", APP_VERSION_MAJOR)
        .replace("{{APP_VERSION}}", APP_VERSION)
        .replace("{{GITHUB_REPO_URL}}", GITHUB_REPO_URL)
        .replace("{{GITHUB_REPO}}", GITHUB_REPO)
    )
    return HTMLResponse(content)


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
async def serve_favicon() -> FileResponse:
    """Serve the brand vector favicon."""
    return FileResponse(str(_static_dir / "icon.svg"), media_type="image/svg+xml")


@limiter.limit("15/minute")
@app.post("/api/analyze")
async def analyze(request: Request, payload: AnalyzeRequest) -> Dict[str, Any]:
    """Analyze a single developer profile."""
    token = payload.github_token or _get_server_token()
    client_ip = _get_client_ip(request)
    return await _run_analysis(payload.username, token, client_ip)


@limiter.limit("8/minute")
@app.post("/api/compare")
async def compare(request: Request, payload: CompareRequest) -> Dict[str, Any]:
    """Compare two developers side-by-side."""
    token = payload.github_token or _get_server_token()
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
    usernames = payload.usernames
    if not usernames:
        raise HTTPException(422, "At least one username required.")
    token = payload.github_token or _get_server_token()
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
                "username": uname,
                "avatar_url": res["profile"]["avatar_url"],
                "name": res["profile"]["name"],
                "score": res["score"]["total"],
                "grade": res["score"]["grade"],
                "archetype": res["archetype"]["label"],
                "archetype_glow": res["archetype"]["glow"],
                "top_language": next(iter(res["languages"]), "N/A"),
                "total_stars": res["stats"]["total_stars"],
                "followers": res["profile"]["followers"],
                "repos": res["stats"]["own_repos"],
                "streak": res["streaks"]["current"],
                "html_url": res["profile"]["html_url"],
            })
    return sorted(out, key=lambda x: x.get("score", -1), reverse=True)


@app.get("/embed/{username}", include_in_schema=False)
async def embed_profile(
    username: str = FPath(
        ...,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
        description="GitHub username (1–39 chars, alphanumeric and hyphens)",
    ),
) -> HTMLResponse:
    """Minimal embeddable profile card for portfolios and READMEs."""
    token = _get_server_token()
    try:
        data = await _run_analysis(username.strip(), token)
    except HTTPException as exc:
        return HTMLResponse(
            f"<p style='font-family:monospace;color:#ef4444;padding:16px'>Error: {_html.escape(str(exc.detail))}</p>",
            status_code=exc.status_code,
        )

    p = data["profile"]
    sc = data["score"]
    arc = data["archetype"]
    langs = list(data["languages"].items())[:4]
    tot = sum(v for _, v in langs) or 1
    grade_colors = {
        "S+": "#f59e0b",
        "S": "#10b981",
        "A": "#06b6d4",
        "B": "#8b5cf6",
        "C": "#f97316",
        "D": "#ef4444",
        "E": "#6b7280",
    }
    sc_col = grade_colors.get(sc["grade"], "#22d3ee")

    p_name = _html.escape(str(p.get("name") or p.get("login", "")))
    p_login = _html.escape(str(p.get("login", "")))
    p_avatar = _html.escape(str(p.get("avatar_url", "")))
    arc_label = _html.escape(str(arc.get("label", "")))
    arc_glow = _html.escape(str(arc.get("glow", "#22d3ee")))
    sc_total = int(sc.get("total", 0))
    sc_grade = _html.escape(str(sc.get("grade", "E")))
    sc_col_e = _html.escape(sc_col)

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
    """Check remaining GitHub API rate limits."""
    headers = _build_headers(_get_server_token())
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await _get_with_retry(client, f"{GITHUB_API}/rate_limit", headers=headers)
        resp.raise_for_status()
        data = resp.json()
    core = data.get("resources", {}).get("core", {})
    return {
        "limit": core.get("limit", 60),
        "remaining": core.get("remaining", 0),
        "reset": core.get("reset", 0),
        "used": core.get("used", 0),
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

    token = _get_server_token()
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
            "found": bool(content.strip()),
            "content": content,
            "html_url": data.get("html_url", ""),
        }


@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, str]:
    """Liveness probe for uptime monitors."""
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/version")
async def version_endpoint() -> Dict[str, str]:
    """Return application version details."""
    return {
        "version": APP_VERSION,
        "short": APP_VERSION_SHORT,
        "major": APP_VERSION_MAJOR,
    }


@app.get("/api/repo-info")
async def repo_info_endpoint() -> Dict[str, Any]:
    """Return Git-Spectre repository details and star count with TTL caching."""
    cache_key = f"repo_info:{GITHUB_REPO}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    headers = _build_headers(_get_server_token())
    fallback = {
        "repo": GITHUB_REPO,
        "url": GITHUB_REPO_URL,
        "stars": 0,
        "forks": 0,
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(8.0)) as client:
        try:
            resp = await client.get(f"{GITHUB_API}/repos/{GITHUB_REPO}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                info = {
                    "repo": GITHUB_REPO,
                    "url": data.get("html_url") or GITHUB_REPO_URL,
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                }
                _cache_set(cache_key, info)
                return info
        except Exception as exc:
            logger.warning("Failed to fetch repo info for %s: %s", GITHUB_REPO, exc)

    return fallback


@limiter.limit("30/minute")
@app.get("/api/leaderboard")
async def leaderboard_endpoint(
    request: Request,
    period: str = "daily",
    limit: int = 50,
    language: Optional[str] = None,
    q: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve ranked developers by check popularity across daily, monthly, yearly, and all-time."""
    valid_periods = {"daily", "monthly", "yearly", "all"}
    clean_period = period.strip().lower()
    if clean_period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Valid options: {', '.join(sorted(valid_periods))}",
        )
    return get_leaderboard(period=clean_period, limit=limit, language=language, query=q)


@limiter.limit("60/minute")
@app.get("/api/leaderboard/languages")
async def leaderboard_languages_endpoint(request: Request) -> Dict[str, Any]:
    """Retrieve distinct programming languages represented across ranked profiles."""
    langs = get_leaderboard_languages()
    return {"total": len(langs), "languages": [l["language"] for l in langs], "details": langs}


@limiter.limit("30/minute")
@app.get("/api/leaderboard/rank/{username}")
async def profile_rank_endpoint(request: Request, username: str) -> Dict[str, Any]:
    """Retrieve rank statistics and check count across all timeframes for a developer."""
    clean_username = _validate_username(username)
    return get_profile_rank(clean_username)


_AVATAR_B64_CACHE: Dict[str, str] = {}


async def _fetch_avatar_b64(avatar_url: Optional[str]) -> Optional[str]:
    """Fetch GitHub avatar and convert to base64 data URI for Camo-safe SVG embedding."""
    if not avatar_url:
        return None

    clean_url = avatar_url.strip()
    if clean_url in _AVATAR_B64_CACHE:
        return _AVATAR_B64_CACHE[clean_url]

    sep = "&" if "?" in clean_url else "?"
    req_url = f"{clean_url}{sep}s=64"

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(req_url, headers={"User-Agent": "Git-Spectre"})
            if resp.status_code == 200 and resp.content:
                content_type = resp.headers.get("content-type", "image/png").split(";")[0].strip()
                b64 = base64.b64encode(resp.content).decode("utf-8")
                data_uri = f"data:{content_type};base64,{b64}"
                if len(_AVATAR_B64_CACHE) > 1000:
                    _AVATAR_B64_CACHE.pop(next(iter(_AVATAR_B64_CACHE)))
                _AVATAR_B64_CACHE[clean_url] = data_uri
                return data_uri
    except Exception as e:
        logger.debug("Could not fetch avatar for badge (%s): %s", clean_url, e)

    return None


@app.get("/api/badge/{username}", include_in_schema=False)
@app.get("/api/badge/card/{username}", include_in_schema=False)
async def badge_svg(
    request: Request,
    username: str = FPath(
        ...,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$",
        description="GitHub username",
    ),
    style: str = "pill",
    metric: str = "score",
    theme: str = "spectre",
    border: bool = True,
) -> Response:
    """
    Return dynamic vector SVG badges and cards for GitHub Profile READMEs.
    Fully compatible with GitHub's Camo image proxy and markdown image embeds.
    """
    # If accessed via /api/badge/card/{username}, default style to card
    if "/api/badge/card/" in request.url.path:
        style = "card"

    clean_user = username.strip()
    style_clean = style.lower().strip()
    metric_clean = metric.lower().strip()
    theme_clean = theme.lower().strip()

    token = _get_server_token()
    data: Optional[Dict[str, Any]] = None

    try:
        data = await _run_analysis(clean_user, token)
    except Exception:
        # Fallback to local SQLite database if live API fails / is rate-limited
        db_profile = get_cached_profile_record(clean_user)
        if db_profile:
            data = {
                "profile": {
                    "login": db_profile["login"],
                    "name": db_profile.get("name"),
                    "avatar_url": db_profile.get("avatar_url"),
                    "public_repos": db_profile.get("public_repos", 0),
                    "stars_earned": db_profile.get("stars_earned", 0),
                },
                "stats": {
                    "total_stars": db_profile.get("stars_earned", 0),
                    "own_repos": db_profile.get("public_repos", 0),
                },
                "score": {
                    "total": db_profile.get("dev_score", 0),
                    "tier": db_profile.get("score_tier", "B"),
                    "grade": db_profile.get("score_tier", "B"),
                },
                "archetype": {
                    "title": db_profile.get("archetype_title", "CODE CRAFTSMAN"),
                    "label": db_profile.get("archetype_title", "CODE CRAFTSMAN"),
                },
                "languages": {db_profile["primary_language"]: 100} if db_profile.get("primary_language") else {},
                "dev_level": {"level": db_profile.get("dev_level", 1)},
                "streaks": {"longest": 0, "current": 0},
            }

    if not data:
        svg = generate_not_found_badge(clean_user, style="card" if style_clean in ("card", "badge", "profile") else "pill", theme=theme_clean)
        return Response(
            svg,
            media_type="image/svg+xml; charset=utf-8",
            headers={"Cache-Control": "public, max-age=120"},
        )

    p = data.get("profile", {})
    sc = data.get("score", {})
    arc = data.get("archetype", {})
    langs = data.get("languages", {})
    streaks = data.get("streaks", {})
    stats_data = data.get("stats", {})
    total_stars = stats_data.get("total_stars")
    if total_stars is None:
        total_stars = sum(
            r.get("stars", 0) or r.get("stargazers_count", 0)
            for r in data.get("top_repos", [])
        ) or p.get("stars_earned", 0)

    # Rank metadata
    try:
        rank_data = get_profile_rank(clean_user)
    except Exception:
        rank_data = None

    if style_clean in ("card", "badge", "profile"):
        # Fetch user's avatar for embedding in profile badge
        avatar_b64 = None
        av_url = p.get("avatar_url") or f"https://avatars.githubusercontent.com/{clean_user}"
        try:
            avatar_b64 = await _fetch_avatar_b64(av_url)
        except Exception:
            avatar_b64 = None

        svg = generate_profile_badge(
            profile=p,
            score=sc,
            archetype=arc,
            languages=langs,
            rank_info=rank_data,
            streaks=streaks,
            total_stars=total_stars,
            theme=theme_clean,
            border=border,
            avatar_b64=avatar_b64,
        )
    else:
        # Determine left / right labels based on selected metric
        tier = str(sc.get("tier") or sc.get("grade") or "B").upper()
        accent_col = GRADE_COLORS.get(tier, "#10b981")

        if metric_clean == "rank":
            rank_num = rank_data.get("all_time", {}).get("rank") if rank_data else None
            rank_display = f"#{rank_num}" if rank_num else "Tracked"
            left_text = "Git-Spectre"
            right_text = f"Rank {rank_display}"
            accent_col = "#06b6d4"
        elif metric_clean == "archetype":
            arc_label = str(arc.get("title") or arc.get("label") or "Craftsman")
            left_text = "Archetype"
            right_text = arc_label
            accent_col = "#8b5cf6"
        elif metric_clean == "level":
            lvl = data.get("dev_level", {}).get("level", 1)
            left_text = "Git-Spectre"
            right_text = f"Level {lvl}"
            accent_col = "#f59e0b"
        elif metric_clean == "streak":
            stk = streaks.get("longest") or streaks.get("current") or 0
            left_text = "Streak"
            right_text = f"{stk} Days"
            accent_col = "#f97316"
        else:
            # Default score + tier
            left_text = "Git-Spectre"
            right_text = f"Score {sc.get('total', 0)} · {tier}"

        pill_style = style_clean if style_clean in ("cyber", "for-the-badge", "flat") else "flat"
        svg = generate_pill_badge(
            left=left_text,
            right=right_text,
            color=accent_col,
            style=pill_style,
            theme=theme_clean,
        )

    is_preview = "_t" in request.query_params or "no-cache" in request.headers.get("cache-control", "")
    cache_header = "no-cache, no-store, must-revalidate" if is_preview else "public, max-age=1800, s-maxage=1800, stale-while-revalidate=86400"

    return Response(
        svg,
        media_type="image/svg+xml; charset=utf-8",
        headers={
            "Cache-Control": cache_header,
        },
    )



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)