"""
tests/test_validators.py
========================
Unit tests for Git-Spectre's pure-function validators and analytics helpers.
Run with: pytest tests/ -v
"""

import pytest
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Import the functions under test
# ---------------------------------------------------------------------------
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import (
    _validate_username,
    _validate_token,
    _compute_archetype,
    _compute_score,
    _compute_streaks,
    _aggregate_languages,
)


# ---------------------------------------------------------------------------
# _validate_username
# ---------------------------------------------------------------------------

class TestValidateUsername:
    def test_valid_simple(self):
        assert _validate_username("torvalds") == "torvalds"

    def test_valid_with_hyphen(self):
        assert _validate_username("git-spectre") == "git-spectre"

    def test_valid_single_char(self):
        assert _validate_username("a") == "a"

    def test_strips_whitespace(self):
        assert _validate_username("  octocat  ") == "octocat"

    def test_invalid_empty(self):
        with pytest.raises(ValueError, match="empty"):
            _validate_username("")

    def test_invalid_starts_with_hyphen(self):
        with pytest.raises(ValueError):
            _validate_username("-invalid")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError):
            _validate_username("user@name")

    def test_invalid_too_long(self):
        with pytest.raises(ValueError):
            _validate_username("a" * 40)

    def test_valid_max_length(self):
        # 39 chars is the max
        name = "a" + "b" * 37 + "c"
        assert _validate_username(name) == name


# ---------------------------------------------------------------------------
# _validate_token
# ---------------------------------------------------------------------------

class TestValidateToken:
    def test_none_passthrough(self):
        assert _validate_token(None) is None

    def test_empty_string_returns_none(self):
        assert _validate_token("") is None
        assert _validate_token("   ") is None

    def test_valid_ghp_token(self):
        token = "ghp_" + "A" * 36
        assert _validate_token(token) == token

    def test_valid_gho_token(self):
        token = "gho_" + "B" * 36
        assert _validate_token(token) == token

    def test_invalid_format_rejected(self):
        with pytest.raises(ValueError, match="Invalid GitHub token"):
            _validate_token("not_a_real_token")

    def test_injection_attempt_rejected(self):
        with pytest.raises(ValueError):
            _validate_token("<script>alert(1)</script>")

    def test_strips_whitespace(self):
        token = "ghp_" + "C" * 36
        assert _validate_token(f"  {token}  ") == token


# ---------------------------------------------------------------------------
# _compute_archetype
# ---------------------------------------------------------------------------

FAKE_PROFILE_BASE = {"followers": 10, "following": 5, "created_at": "2020-01-01T00:00:00Z"}

class TestComputeArchetype:
    def _make_repos(self, stars=0, count=1, fork=False):
        return [{"stargazers_count": stars, "fork": fork, "language": "Python", "size": 1000}
                for _ in range(count)]

    def test_open_source_legend(self):
        repos = self._make_repos(stars=1000)
        result = _compute_archetype({"Python": 1000}, repos, FAKE_PROFILE_BASE)
        assert result["label"] == "OPEN-SOURCE LEGEND"

    def test_community_beacon(self):
        profile = {**FAKE_PROFILE_BASE, "followers": 500}
        result = _compute_archetype({"Python": 1000}, self._make_repos(), profile)
        assert result["label"] == "COMMUNITY BEACON"

    def test_polyglot(self):
        langs = {f"Lang{i}": 1000 for i in range(8)}
        result = _compute_archetype(langs, self._make_repos(), FAKE_PROFILE_BASE)
        assert result["label"] == "THE POLYGLOT"

    def test_specialist(self):
        langs = {"Python": 9000, "Shell": 1000}
        result = _compute_archetype(langs, self._make_repos(), FAKE_PROFILE_BASE)
        assert "SPECIALIST" in result["label"]

    def test_code_craftsman_fallback(self):
        # Two languages with equal bytes → no specialist (< 80%), low stars, low followers
        langs = {"Python": 500, "Shell": 500}
        result = _compute_archetype(langs, self._make_repos(), FAKE_PROFILE_BASE)
        assert result["label"] == "CODE CRAFTSMAN"


# ---------------------------------------------------------------------------
# _compute_streaks
# ---------------------------------------------------------------------------

class TestComputeStreaks:
    def _push_event(self, date_str):
        return {
            "type": "PushEvent",
            "created_at": f"{date_str}T12:00:00Z",
            "payload": {"commits": [{"message": "test"}]},
        }

    def test_empty_events(self):
        result = _compute_streaks([])
        assert result == {"current": 0, "longest": 0, "total_active_days": 0}

    def test_non_push_events_ignored(self):
        events = [{"type": "WatchEvent", "created_at": "2026-01-01T12:00:00Z"}]
        result = _compute_streaks(events)
        assert result["total_active_days"] == 0

    def test_total_active_days_counted(self):
        events = [self._push_event("2026-01-01"), self._push_event("2026-01-03")]
        result = _compute_streaks(events)
        assert result["total_active_days"] == 2

    def test_longest_streak_consecutive(self):
        events = [self._push_event(f"2026-01-0{i}") for i in range(1, 6)]
        result = _compute_streaks(events)
        assert result["longest"] == 5


# ---------------------------------------------------------------------------
# _aggregate_languages
# ---------------------------------------------------------------------------

class TestAggregateLanguages:
    def test_skips_forks(self):
        repos = [
            {"fork": True,  "language": "Python", "size": 9999},
            {"fork": False, "language": "Python", "size": 100},
        ]
        result = _aggregate_languages(repos)
        assert result == {"Python": 100}

    def test_skips_repos_with_no_language(self):
        repos = [{"fork": False, "language": None, "size": 500}]
        result = _aggregate_languages(repos)
        assert result == {}

    def test_aggregates_multiple_repos(self):
        repos = [
            {"fork": False, "language": "Python", "size": 300},
            {"fork": False, "language": "Python", "size": 200},
            {"fork": False, "language": "TypeScript", "size": 100},
        ]
        result = _aggregate_languages(repos)
        assert result["Python"] == 500
        assert result["TypeScript"] == 100

    def test_sorted_descending(self):
        repos = [
            {"fork": False, "language": "Go",     "size": 50},
            {"fork": False, "language": "Python", "size": 500},
        ]
        result = _aggregate_languages(repos)
        assert list(result.keys())[0] == "Python"
