"""
tests/test_badge.py
===================
Unit and integration tests for GitHub Profile Badge & Dossier Card generation:
- Camo-compatible vector SVG markup validity
- Pill Badge generation across flat, cyber, and for-the-badge styles
- Dossier Profile Card generation across themes
- Caching headers and HTTP response validation
- Database fallback when live API is unavailable
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from core.badge import (
    GRADE_COLORS,
    THEMES,
    generate_dossier_card,
    generate_not_found_badge,
    generate_pill_badge,
)
from core.cache import _cache_clear
from core.leaderboard import _get_connection, init_leaderboard_db
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """Use an isolated SQLite test database for each test function."""
    _cache_clear()
    test_db = tmp_path / "test_badge_leaderboard.db"
    monkeypatch.setattr("core.leaderboard._get_db_path", lambda: test_db)
    init_leaderboard_db()
    yield test_db
    _cache_clear()


# ============================================================================
# Unit Tests: generate_pill_badge
# ============================================================================

class TestPillBadgeGeneration:
    def test_flat_pill_valid_svg(self):
        svg = generate_pill_badge("Git-Spectre", "Score 850 · S", color="#10b981", style="flat")
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert 'role="img"' in svg
        assert "Git-Spectre" in svg
        assert "Score 850 · S" in svg
        # Verify valid XML
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"

    def test_cyber_pill_valid_svg(self):
        svg = generate_pill_badge("Archetype", "The Polyglot", color="#8b5cf6", style="cyber", theme="spectre")
        assert 'height="24"' in svg
        assert "The Polyglot" in svg
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"

    def test_for_the_badge_pill_valid_svg(self):
        svg = generate_pill_badge("Rank", "#1", color="#06b6d4", style="for-the-badge")
        assert 'height="28"' in svg
        assert "RANK" in svg
        assert "#1" in svg
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"

    def test_html_escaping_in_pill(self):
        svg = generate_pill_badge("User <script>", "Score & >", color="#ff0000")
        assert "<script>" not in svg
        assert "&lt;script&gt;" in svg
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"


# ============================================================================
# Unit Tests: generate_dossier_card
# ============================================================================

class TestDossierCardGeneration:
    def test_dossier_card_valid_svg_and_dimensions(self):
        profile = {
            "login": "octocat",
            "name": "The Octocat",
            "public_repos": 8,
            "stars_earned": 1250,
        }
        score = {"total": 840, "tier": "S"}
        archetype = {"title": "The Polyglot"}
        languages = {"Python": 50000, "TypeScript": 30000, "Rust": 20000}
        rank_info = {"all_time_rank": 42}
        streaks = {"longest": 28}

        svg = generate_dossier_card(
            profile=profile,
            score=score,
            archetype=archetype,
            languages=languages,
            rank_info=rank_info,
            streaks=streaks,
            total_stars=1250,
            theme="spectre",
        )

        assert 'height="46"' in svg
        assert "The Octocat" in svg
        assert "840 XP" in svg
        assert "1,250" in svg
        assert "Python" in svg
        assert "Polyglot" in svg

        # XML Parsing verification
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"

    def test_dossier_card_with_avatar(self):
        profile = {"login": "testdev", "name": "Test Developer"}
        score = {"total": 950, "tier": "S+"}
        avatar_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        svg = generate_dossier_card(
            profile=profile,
            score=score,
            avatar_b64=avatar_b64,
            theme="spectre",
        )
        assert "data:image/png;base64," in svg
        assert "av-clip-testdev" in svg
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"

    def test_dossier_card_themes(self):
        profile = {"login": "torvalds"}
        score = {"total": 980, "tier": "S+"}
        for theme_name in THEMES:
            svg = generate_dossier_card(profile, score, theme=theme_name)
            assert 'height="46"' in svg
            tree = ET.fromstring(svg)
            assert tree.tag == "{http://www.w3.org/2000/svg}svg"

    def test_not_found_card(self):
        svg = generate_not_found_badge("ghost_user", style="card", theme="spectre")
        assert "User Not Found: @ghost_user" in svg
        assert "ghost_user" in svg
        tree = ET.fromstring(svg)
        assert tree.tag == "{http://www.w3.org/2000/svg}svg"


# ============================================================================
# Integration Tests: FastAPI Route /api/badge/{username}
# ============================================================================

class TestBadgeRoute:
    def test_badge_fallback_when_not_found(self):
        resp = client.get("/api/badge/nonexistentuser999")
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers.get("content-type", "")
        assert "max-age" in resp.headers.get("cache-control", "")
        assert "not found" in resp.text.lower()

    def test_badge_card_route_fallback(self):
        resp = client.get("/api/badge/card/nonexistentuser999")
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers.get("content-type", "")
        assert "User Not Found" in resp.text

    def test_badge_from_database_record(self, monkeypatch):
        # Simulate GitHub API being offline/rate-limited to test DB fallback
        async def mock_offline_analysis(u, t):
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="GitHub API Offline")

        monkeypatch.setattr("main._run_analysis", mock_offline_analysis)

        # Insert a profile into leaderboard_profiles
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO leaderboard_profiles (
                    login, name, avatar_url, dev_score, score_tier,
                    archetype_title, archetype_badge, dev_level,
                    primary_language, public_repos, stars_earned, followers,
                    first_checked_at, last_checked_at
                ) VALUES (
                    'testcoder', 'Test Coder', 'https://example.com/avatar.png', 890, 'S',
                    'Code Architect', '', 15,
                    'Python', 25, 450, 120,
                    1700000000.0, 1700000000.0
                );
                """
            )

        # 1. Pill badge
        resp = client.get("/api/badge/testcoder")
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.headers.get("content-type", "")
        assert "890" in resp.text
        assert "S" in resp.text
        assert "1800" in resp.headers.get("cache-control", "")

        # 2. Card badge via query param
        card_resp = client.get("/api/badge/testcoder?style=card&theme=matrix")
        assert card_resp.status_code == 200
        assert 'height="46"' in card_resp.text
        assert "Test Coder" in card_resp.text
        assert "450" in card_resp.text
        assert "890" in card_resp.text
        assert "Python" in card_resp.text

        # 3. Card badge via direct alias route
        alias_resp = client.get("/api/badge/card/testcoder")
        assert alias_resp.status_code == 200
        assert 'height="46"' in alias_resp.text
        assert "Test Coder" in alias_resp.text

        # 4. Pill badge with archetype metric
        arc_resp = client.get("/api/badge/testcoder?metric=archetype")
        assert arc_resp.status_code == 200
        assert "Code Architect" in arc_resp.text

