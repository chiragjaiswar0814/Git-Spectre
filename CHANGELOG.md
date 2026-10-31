# Changelog

All notable changes to Git-Spectre are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.1.1] — 2026-10-28

### Added

- **Turso (LibSQL Cloud) Database Integration (`core/leaderboard.py`)**:
    - Implemented cloud-native persistence for the Global Developer Leaderboard on serverless hosting platforms (Vercel, AWS Lambda), resolving ephemeral `/tmp` storage resets across container cold starts, multi-instance routing, and page refreshes.
    - Added high-performance `TursoHTTPConnection`, `TursoCursor`, and `TursoRow` adapters in `core/leaderboard.py`, communicating natively with Turso's official `/v2/pipeline` HTTP API using existing `httpx` client infrastructure with zero extra binary C/Rust compilation requirements.
    - Automatic dual-mode database resolution: connects securely to Turso cloud when `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` are configured, while seamlessly preserving local SQLite file fallback (`data/leaderboard.db`) for offline development.
    - Added environment variable documentation in `.env.example` for `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`.
- **Automated Test Suite Expansion (`tests/test_leaderboard.py`)**:
    - Added unit tests for `TursoRow` mapping, `TursoCursor` iteration, and Turso pipeline type encoding/decoding (`TestTursoAdapter`).
    - Hardened test isolation in `isolated_db` fixture, ensuring cloud database environment variables never contaminate local unit test suites.

---

## [3.1.0] — 2026-10-26


### Added

- **Global Developer Leaderboard & Popularity Ranking System**:
    - Implemented a community-driven developer leaderboard ranking analyzed GitHub profiles based on verified check count (trending community interest), with secondary tie-breakers on Developer Score™ and total stars earned.
    - Multi-window timeframe filtering supporting **Today (`daily`)**, **This Month (`monthly`)**, **This Year (`yearly`)**, and **All-Time (`all`)**.
    - **Embedded SQLite Storage (`core/leaderboard.py`)**: Dual-table architecture (`leaderboard_profiles` and `profile_checks`) with Write-Ahead Logging (`WAL`) mode, sub-millisecond query performance, zero cloud database dependencies, and transparent `/tmp/spectre_leaderboard.db` fallback for serverless deployments (Vercel, AWS Lambda).
    - **Hardened Anti-Spam & Anti-Gaming Defense**:
        - Compound unique index `idx_unique_daily_check (ip_hash, login, date_utc)` enforcing database-level idempotency: automated loops and repeat checks from the same client IP on the same UTC day return full profile analyses but increment zero check counts.
        - Salted SHA-256 IP hashing (`_hash_client_ip`) with daily salt rotation and date mixing for GDPR/privacy compliance with zero persistence of raw IP addresses.
        - Profile eligibility gatekeeper (`is_profile_eligible`) filtering bot accounts (`[bot]`, `type == 'Bot'`), organizations (`type == 'Organization'`), and zero-activity hollow accounts.
    - **New REST API Endpoints**:
        - `GET /api/leaderboard`: Query ranked profiles by `period`, `limit`, `language`, and `q` search query with rate limiting.
        - `GET /api/leaderboard/languages`: Retrieve distinct primary programming languages across all ranked developers with real-time representation counts.
        - `GET /api/leaderboard/rank/{username}`: Fetch a developer's real-time rank and check metrics across all timeframes.
    - **Dynamic Language Filter & Multi-Tier Request Caching Engine**:
        - Replaced hardcoded language dropdown options with dynamic aggregation querying `SELECT primary_language, COUNT(*) FROM leaderboard_profiles GROUP BY primary_language`.
        - Server-side in-memory TTL caching (`core/cache.py`) with prefix-based invalidation (`_cache_delete_prefix("leaderboard:")`) eliminating redundant SQLite table scans, with automatic cache invalidation whenever new profile checks are committed.
        - Client-side in-memory request cache (`static/js/api.js`) with 60s TTL and LRU eviction, eliminating duplicate network fetches and API spam when users toggle between `Today`, `This Month`, `This Year`, and `All-Time`.
        - Instantaneous zero-latency tab switching for cached periods without layout shifts, spinner flashes, or empty header flicker.
    - **Dedicated Full-Page Rankings View (`static/js/components/leaderboard.js`)**:
        - Full-page responsive SPA view (`#leaderboardSection` / `/?view=leaderboard`) replacing modal overlay for an expansive, focused developer browsing experience.
        - Clean executive-grade UI/UX with professional typography, zero emoji usage, and refined SVG vector iconography.
        - Interactive segmented timeframe switcher (`Today`, `This Month`, `This Year`, `All-Time`).
        - Top 3 developer podium with sleek metallic badge accents (`#01`, `#02`, `#03`), dev grade chips, score metrics, dominant language tag, and verified check count indicators.
        - Full ranked developer table with live search, language selector chips, and instant click-to-scan navigation into complete profile dossiers.
        - Real-time rank pill in the developer dossier identity card that navigates directly to the Rankings page.
        - Global keyboard shortcut `Ctrl+L` for instant navigation to Developer Rankings.
    - **Dedicated Database Documentation (`docs/SCHEMA.md`)**:
        - Comprehensive schema specification, ERD diagram, index definitions, anti-spam security architecture, query patterns, and serverless migration policies.
- **Premium Modern Custom Scrollbars**:
    - Designed sleek, modern custom scrollbars with smooth scroll behavior and `scrollbar-gutter: stable` to eliminate page shifting during view transitions.
    - Implemented thin rounded scrollbars (7px global, 4px `.scroll-thin`) with transparent tracks, padded thumb clips, and dynamic hover/active accent states across dark and light themes.
- **Decluttered Header & Grouped Navigation Bar**:
    - Redesigned the top navigation bar into 3 distinct, well-spaced functional clusters separated by subtle vertical dividers (`h-4 w-px bg-line/60`):
        - _Tools Group_: Ghost pill buttons for `Compare` and `Batch` screener with responsive labels and icons.
        - _Telemetry & Community Group_: Streamlined live API rate limit capsule and GitHub repository star counter badge.
        - _Controls & Settings Group_: Clean theme toggle and GitHub Personal Access Token Vault button.
    - Eliminated visual clutter and "border soup" by standardizing control heights (`h-8`), subtle translucent backgrounds (`bg-surface/50`), and balanced horizontal padding.
    - Implemented a sleek mobile hamburger dropdown drawer (`#navMobileDrawer`) and trigger (`#navMobileMenuBtn`) on mobile screens (< 640px) while keeping the GitHub star button prominently visible outside in the top bar.
    - Added full labeled navigation items in the mobile drawer for `Compare Developers`, `Batch Screener`, `API Vault Token` (with live PAT status badge), `Appearance Theme`, and a mobile-accessible live GitHub API Quota telemetry progress bar.
    - Configured click-outside and Escape key auto-dismissal for the mobile navigation drawer.
- **Clean Home Navigation & URL State Management**:
    - Configured home/logo navigation (`navLogoBtn` and `setView('hero')`) to automatically strip `/?u=username` query parameters from the browser address bar via `history.pushState(null, '', window.location.pathname)`.
    - Added reset of the search input field upon returning to the hero view.
    - Added `popstate` event listener to handle smooth browser Back and Forward history transitions between profile scans and the hero view.
- **GitHub Repository Link & Live Star Counter**:
    - Added repository star button in the navigation bar with GitHub octocat icon and live stargazers count badge.
    - Implemented `GET /api/repo-info` endpoint with server-side caching (`_cache_set`/`_cache_get`) to query and return GitHub repository metadata, stars, and forks while respecting API rate limits.
    - Added `syncRepoInfo()` in `static/js/components/nav.js` and `getRepoInfo()` in `static/js/api.js` to dynamically synchronize the repository link and live star count.

### Changed

- **Modular Backend Architecture (`core/` package)**:
    - Decomposed the monolithic 1,568-line `main.py` into dedicated, single-responsibility modules under `core/`:
        - `core/config.py`: Environment configuration, tokens, constants, and logging setup.
        - `core/cache.py`: In-memory TTL response caching logic.
        - `core/schemas.py`: Pydantic request models, PAT regexes, and username sanitization.
        - `core/fetchers.py`: Asynchronous GitHub REST scrapers and exponential back-off network client.
        - `core/analytics.py`: Developer Score™ composite calculation, archetype classification, heatmap, streak analysis, and repo intelligence.
        - `core/gamification.py`: XP leveling, unlockable achievement badges, GitHub Wrapped, and social graph computation.
        - `core/service.py`: Pipeline orchestrator running end-to-end user profile analysis.
    - Reduced `main.py` from 1,568 lines to 408 lines focused solely on FastAPI application configuration, security middleware, rate limiting, and route dispatching.
    - Every backend source file now strictly obeys the project's `< 500 lines of code` standard while maintaining 100% backwards compatibility with existing test suites and deployment setups.
- **Centralized Dynamic Versioning (Single Source of Truth)**:
    - Eliminated hardcoded version numbers across `index.html`, `main.py`, `core/fetchers.py`, and `README.md`.
    - Introduced `APP_VERSION`, `APP_VERSION_SHORT`, and `APP_VERSION_MAJOR` constants in `core/config.py` (configurable via `APP_VERSION` environment variable).
    - Added `GET /api/version` endpoint to programmatically expose runtime version metadata.
    - Dynamically inject version metadata when serving the SPA in `serve_spa()` and synchronize badges on the client via `nav.js:syncVersion()`.
    - Updated User-Agent headers in `core/fetchers.py` to use dynamic `APP_VERSION`.

### Removed

- **Legacy Developer Tooling Scripts (`scripts/gen_html.py`, `scripts/fix_js.py`)**:
    - Removed `scripts/gen_html.py`: Legacy v2 HTML generator that outputted a monolithic single-file bundle. Following the Git-Spectre v3.0 architecture overhaul that decoupled the frontend into modular ES modules (`static/js/components/`, `static/js/export/`, and `static/css/theme.css`), this script was obsolete and hazardous (running it would overwrite the modern 256-line `index.html` with monolithic v2 code).
    - Removed `scripts/fix_js.py`: One-time hotfix script patching an HSL string bug in the monolithic `index.html` that is no longer present in the codebase.
    - Removed the `scripts/` directory and cleaned up references in `.vercelignore`.

---

## [3.0.0] — 2026-10-19

### Added — Step 1: Gamification Layer

- **Developer Level System** — XP-based ranking from Intern → Junior → Mid → Senior → Staff → Principal → Legend, derived from Dev Score™. Animated XP ring + progress bar with pulsing rank label.
- **15 Achievement Badges** — Unlockable with rarity tiers (Common / Rare / Epic / Legendary):
    - 🦉 Night Owl, 🔥 Streak King, 🌐 Polyglot, 🌍 Open Source Hero
    - 🤝 Community Builder, ⭐ Star Collector, 🍴 Fork Collector, 🧙 Gist Wizard
    - 🔀 External Contributor, 📅 GitHub Veteran, 📦 Prolific Creator
    - 🏆 Legend, 💯 Centurion, 🌅 Early Adopter, ⚡ Marathon Runner
- Locked badges shown in grayscale; unlocked badges animate in with spring bounce effect.
- Rarity glow: Legendary (red), Epic (purple), Rare (blue).
- Backend: `_compute_achievements()`, `_compute_dev_level()` in `main.py`.
- Version bump in navbar and hero badge: **v3.0**.

### Added — UI/UX Overhaul & Modular Frontend Architecture

- **Strict File Limit Standard** — Decoupled monolithic `index.html` (formerly 2,200+ lines) into clean, standalone ES modules under `static/js/components/` and `static/js/export/`. Every source file strictly obeys `< 500 lines of code` (`index.html` reduced to ~256 lines).
- **Interactive Telemetry Grid Canvas** — Dynamic mouse-tracking telemetry background with distance-decay grid points, pulse radar sweep, and noise overlay.
- **Brand Vector Identity** — Added dedicated vector assets `static/icon.svg` (favicon) and `static/text-icon.svg` (logo with gradient fill), replacing previous emoji/text placeholders.
- **Red / Crimson Palette Theme** — Modern cinematic theme with tailored tokens in `static/css/theme.css`.

### Added — Client-Side Export Subsystem

- **Native Canvas 2D Share Card** — Rebuilt share card generation using high-resolution Canvas 2D with vector icons, radial gradient background, avatar rendering, score ring, and developer archetype pill.
- **Multi-Page Vector PDF Dossier** — Integrated 2-page vector PDF generation via jsPDF:
    - Page 1: Developer header, composite score breakdown, commit quality, language distribution, top repos.
    - Page 2: Contribution streak metrics, activity distribution, tech stack DNA, and community stats.

### Improved — Modals & Batch Screener

- **Dynamic Modal Templates** — Extracted modal DOM trees into `modalTemplates.js` and `scanOverlay.js`, injected on demand.
- **Batch Screener Table Layout** — Widened modal container to responsive `max-w-4xl`, aligned score and grade horizontally with `whitespace-nowrap`, and styled grades with tier-colored badges (S+, S, A, B, C, D, E).

---

## [2.2.1] — 2026-10-08

### Security

- **XSS fix** — `/embed/{username}` and `/api/badge/{username}` now escape all
  GitHub-sourced strings (name, login, archetype label, language names) with
  `html.escape()` before injecting into HTML/SVG output.
- **Token validation** — `github_token` in all request bodies is now validated
  against the GitHub PAT format regex (`ghp_`, `gho_`, `ghu_`, `ghr_`, `ghs_`).
  Invalid strings are rejected with HTTP 422 before they reach GitHub's API.
- **Path parameter validation** — `/embed/{username}`, `/api/readme/{username}`,
  and `/api/badge/{username}` now enforce the same username regex used by POST
  body validators (letters, numbers, hyphens, 1–39 chars).
- **Rate limiter IP fix** — `slowapi` now reads the real client IP from the
  `X-Forwarded-For` header (set by Vercel's proxy), preventing all users from
  sharing a single rate-limit bucket.
- **Security headers** — Every response now includes `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, and `X-XSS-Protection` headers.

### Added

- `GET /health` — Liveness probe endpoint returning `{"status": "ok", "version": "2.2"}`.
- `.python-version` file — pins the interpreter to Python 3.11 for pyenv / Vercel.
- `scripts/` directory — developer tooling scripts (`gen_html.py`, `fix_js.py`)
  are now located here to keep the project root clean.
- `CONTRIBUTING.md` — contributor guide covering local setup, testing, and PR process.
- `requirements-dev.txt` — development-only dependencies (pytest, pytest-asyncio, respx).
- `tests/` — unit tests for pure analytics functions and input validators.

### Changed

- `vercel.json` — added `maxLambdaSize: "15mb"` to prevent bundle size warnings.

---

## [2.2] — 2026-10-XX

### Added

- **Peak Coding Persona** — 🌙 Night Owl / 🌅 Early Bird / ☀️ 9-to-5 Dev / 🌆 Evening Coder.
- **Star Velocity** — Stars earned per year of account existence shown under Stars stat.
- **Dev Roast** — Data-grounded 2-sentence humorous roast in the archetype card.
- **Social Graph** — Mutual follows, fans (followers-not-followed), and unrequited.
- **Profile README API** — `GET /api/readme/{username}`.
- **GitHub Wrapped** — Year-in-review highlights panel.
- **README Quality Score** — 0–100 signal-based score for the user's profile README.
- **Dynamic SVG badge** — `GET /api/badge/{username}` for embedding in READMEs.

---

## [2.1] — 2026-09-XX

### Added

- GitHub URL input — paste full profile URL, extracts handle automatically.
- Search history — last 10 scans saved in `localStorage`.
- Commit message quality rating (0–100).
- Community activity panel (PRs, issues, comments, external pushes).
- Fork analysis panel with health indicators.
- Repo health badges (🟢 Active / 🟡 Stale / 🔴 Archived).
- Chronotype badge.
- Radar dual-view (KB vs. repo count).
- Shareable PNG card and shareable URL (`/?u={username}`).
- Batch screener — rank up to 10 profiles concurrently.
- Embed widget — `GET /embed/{username}`.
- Keyboard shortcuts (`Ctrl+K`, `Ctrl+E`, `Ctrl+D`, `Ctrl+B`, `Ctrl+T`).
- Dark / Light mode toggle.
- Rate-limit countdown gauge.

---

## [2.0] — 2026-08-XX

### Added

- In-memory TTL cache (5 min) to reduce redundant GitHub API calls.
- `_fetch_events` — push events for heatmap, streaks, and activity hours.
- `_fetch_orgs` — organisation membership.
- `_fetch_gists` — gist analytics.
- Developer Score™ (0–1000 weighted composite).
- Contribution heatmap (date → commit count).
- Activity hour grid (7×24 matrix).
- Streak analysis (current / longest / total active days).
- Tech tag cloud (aggregated repo topics).
- Language evolution chart (per-year breakdown).
- `POST /api/compare` — two users side-by-side.
- `GET /api/rate-limit` — live rate limit status.

---

## [1.0] — Initial release

- FastAPI backend with async parallel GitHub scraping via `asyncio.gather`.
- Language distribution radar chart.
- Developer Archetype engine.
- Top-repos panel.
- Single-file `index.html` frontend using Vanilla JS + TailwindCSS CDN.
