"""
core/service.py
===============
Core analysis orchestration service connecting fetchers, analytics,
gamification, and response caching.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from core.analytics import (
    _aggregate_languages,
    _aggregate_topics,
    _compute_activity_hours,
    _compute_archetype,
    _compute_community,
    _compute_fork_details,
    _compute_heatmap,
    _compute_lang_repo_counts,
    _compute_peak_hour,
    _compute_roast,
    _compute_score,
    _compute_star_velocity,
    _compute_streaks,
    _extract_commit_messages,
    _gist_stats,
    _language_evolution,
    _top_repos,
)
from core.cache import _cache_get, _cache_set
from core.config import TIMEOUT, logger
from core.fetchers import (
    _build_headers,
    _fetch_contribution_calendar,
    _fetch_events,
    _fetch_followers,
    _fetch_following,
    _fetch_gists,
    _fetch_orgs,
    _fetch_profile,
    _fetch_readme_for_quality,
    _fetch_repos,
    _fetch_starred_repos,
)
from core.gamification import (
    _compute_achievements,
    _compute_dev_level,
    _compute_readme_quality,
    _compute_social_graph,
    _compute_wrapped,
)
from core.leaderboard import get_profile_rank, record_profile_check


async def _run_analysis(
    username: str, token: Optional[str], client_ip: Optional[str] = None
) -> Dict[str, Any]:
    """Full profile analysis. Checks TTL cache first."""
    cache_key = f"{username.lower()}:{bool(token)}"
    cached = _cache_get(cache_key)
    if cached:
        if client_ip:
            try:
                record_profile_check(
                    profile=cached.get("profile", {}),
                    score=cached.get("score", {}),
                    client_ip=client_ip,
                    archetype=cached.get("archetype"),
                    dev_level=cached.get("dev_level"),
                    languages=cached.get("languages"),
                    stars_earned=cached.get("stars", {}).get("total_earned", 0),
                )
            except Exception:
                pass
        return {**cached, "cached": True}

    headers = _build_headers(token)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            (
                profile,
                repos,
                events,
                orgs,
                gists,
                followers_raw,
                following_raw,
                starred_raw,
                cal_heatmap,
            ) = await asyncio.gather(
                _fetch_profile(client, username, headers),
                _fetch_repos(client, username, headers),
                _fetch_events(client, username, headers),
                _fetch_orgs(client, username, headers),
                _fetch_gists(client, username, headers),
                _fetch_followers(client, username, headers),
                _fetch_following(client, username, headers),
                _fetch_starred_repos(client, username, headers),
                _fetch_contribution_calendar(client, username),
            )
        except HTTPException:
            raise
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                exc.response.status_code, f"GitHub returned {exc.response.status_code}."
            )
        except Exception as exc:
            logger.exception("Unexpected error for '%s'", username)
            raise HTTPException(502, f"Unexpected error: {exc}")

    lang_bytes = _aggregate_languages(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    streaks_data = _compute_streaks(events)

    result: Dict[str, Any] = {
        "cached": False,
        "profile": {
            "login": profile.get("login"),
            "name": profile.get("name") or profile.get("login"),
            "bio": profile.get("bio") or "No bio provided.",
            "avatar_url": profile.get("avatar_url"),
            "html_url": profile.get("html_url"),
            "location": profile.get("location") or "Unknown",
            "company": profile.get("company") or "Independent",
            "blog": profile.get("blog") or "",
            "twitter": profile.get("twitter_username") or "",
            "created_at": profile.get("created_at", "")[:4],
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "public_repos": profile.get("public_repos", 0),
        },
        "stats": {
            "total_stars": total_stars,
            "total_repos": len(repos),
            "own_repos": len([r for r in repos if not r.get("fork")]),
            "forked_repos": len([r for r in repos if r.get("fork")]),
        },
        "languages": dict(list(lang_bytes.items())[:8]),
        "archetype": _compute_archetype(lang_bytes, repos, profile),
        "top_repos": _top_repos(repos, n=6),
        "score": _compute_score(lang_bytes, repos, profile, events),
        # Heatmap: calendar scrape (full year, level-based) merged with events data
        # (exact commit counts for recent dates override the level approximation)
        "heatmap": {**cal_heatmap, **_compute_heatmap(events)},
        "activity_hours": _compute_activity_hours(events),
        "streaks": streaks_data,
        "topics": _aggregate_topics(repos),
        "lang_evolution": _language_evolution(repos),
        "gists": _gist_stats(gists),
        "commit_messages": _extract_commit_messages(events),
        "community": _compute_community(events, username),
        "fork_details": _compute_fork_details(repos),
        "lang_repo_counts": _compute_lang_repo_counts(repos),
        "peak_hour": _compute_peak_hour(events),
        "star_velocity": _compute_star_velocity(repos, profile),
        "roast": _compute_roast(lang_bytes, repos, profile, events, streaks_data),
        "social_graph": _compute_social_graph(followers_raw, following_raw),
        "pr_merge_rate": (
            lambda opened, merged: round(merged / opened * 100) if opened else None
        )(
            sum(
                1
                for e in events
                if e.get("type") == "PullRequestEvent"
                and e.get("payload", {}).get("action") == "opened"
            ),
            sum(
                1
                for e in events
                if e.get("type") == "PullRequestEvent"
                and e.get("payload", {}).get("action") == "closed"
                and e.get("payload", {}).get("pull_request", {}).get("merged")
            ),
        ),
        "orgs": [
            {
                "login": o["login"],
                "avatar_url": o.get("avatar_url", ""),
                "url": f"https://github.com/{o['login']}",
            }
            for o in orgs[:8]
        ],
        "followers_list": [
            {
                "login": f["login"],
                "avatar_url": f.get("avatar_url", ""),
                "url": f.get("html_url", f"https://github.com/{f['login']}"),
            }
            for f in followers_raw[:10]
        ],
        "following_list": [
            {
                "login": f["login"],
                "avatar_url": f.get("avatar_url", ""),
                "url": f.get("html_url", f"https://github.com/{f['login']}"),
            }
            for f in following_raw[:10]
        ],
        "starred_repos": [
            {
                "name": r.get("full_name") or r.get("name", ""),
                "url": r.get("html_url", ""),
                "stars": r.get("stargazers_count", 0),
                "language": r.get("language") or "",
                "description": (r.get("description") or "")[:80],
            }
            for r in starred_raw[:30]
        ],
    }

    # README quality — fetch separately (not parallel to avoid extra API hit on cache hits)
    readme_raw = await _fetch_readme_for_quality(username, headers)
    result["readme_quality"] = _compute_readme_quality(readme_raw)

    # GitHub Wrapped
    result["wrapped"] = _compute_wrapped(
        repos,
        events,
        profile,
        streaks_data,
        lang_bytes,
        result["heatmap"],
    )

    # Gamification: achievements + developer level
    gists_stats = result["gists"]
    result["achievements"] = _compute_achievements(
        lang_bytes,
        repos,
        profile,
        events,
        streaks_data,
        gists_stats,
    )
    result["dev_level"] = _compute_dev_level(result["score"]["total"])

    # Record check in Leaderboard & attach rank metadata
    try:
        record_profile_check(
            profile=profile,
            score=result["score"],
            client_ip=client_ip or "127.0.0.1",
            archetype=result.get("archetype"),
            dev_level=result.get("dev_level"),
            languages=result.get("languages"),
            stars_earned=result.get("stats", {}).get("total_stars", 0),
        )
        result["leaderboard"] = get_profile_rank(username)
    except Exception as e:
        logger.warning("Leaderboard recording skipped: %s", e)

    _cache_set(cache_key, result)
    return result
