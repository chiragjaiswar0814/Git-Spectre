# Changelog

All notable changes to Git-Spectre are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
