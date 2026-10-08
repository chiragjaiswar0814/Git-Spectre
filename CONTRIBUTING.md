# Contributing to Git-Spectre

Thank you for considering a contribution! Here's everything you need to know.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Running Locally](#running-locally)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Submitting a PR](#submitting-a-pr)
- [Filing Issues](#filing-issues)
- [Known Limitations](#known-limitations)

---

## Getting Started

**Prerequisites:** Python 3.11+, Git.

```bash
git clone https://github.com/chiragjaiswar0814/Git-Spectre.git
cd Git-Spectre

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux

# Install runtime dependencies
pip install -r requirements.txt

# Install dev dependencies (testing)
pip install -r requirements-dev.txt
```

---

## Running Locally

```bash
uvicorn main:app --reload
```

- **UI** → `http://localhost:8000/`
- **API docs** → `http://localhost:8000/docs` *(disabled in production)*
- **Health check** → `http://localhost:8000/health`

Optionally set a default GitHub PAT to raise the rate limit:

```powershell
# Windows PowerShell
$env:GITHUB_TOKEN = "ghp_your_token"
uvicorn main:app --reload
```

---

## Running Tests

```bash
pytest tests/ -v
```

The test suite covers:
- Input validators (`_validate_username`, `_validate_token`)
- Pure analytics functions (`_compute_score`, `_compute_archetype`, `_compute_streaks`)
- HTTP edge cases mocked with `respx`

---

## Project Structure

```
Git-Spectre/
├── main.py              # FastAPI backend — all API logic
├── index.html           # Frontend SPA (generated, do not edit directly)
├── scripts/
│   ├── gen_html.py      # Generates index.html from source templates
│   └── fix_js.py        # Post-processes JS in generated HTML
├── tests/
│   └── test_validators.py
├── requirements.txt     # Runtime dependencies
├── requirements-dev.txt # Dev / test dependencies
├── vercel.json          # Vercel deployment config
├── .python-version      # Python version pin (3.11)
├── .env.example         # Environment variable reference
├── CHANGELOG.md
└── LICENSE
```

> **Note:** `index.html` is the compiled output of `scripts/gen_html.py`.
> If you need to modify the frontend, edit the source in `scripts/gen_html.py`
> and regenerate: `python scripts/gen_html.py`.

---

## Code Style

- **Python:** Follow PEP 8. Type hints are required for all public functions.
- **Line length:** 100 characters.
- **Async:** All I/O must go through `asyncio` / `httpx.AsyncClient`. No `requests` or `time.sleep`.
- **Error handling:** Raise `HTTPException` for expected errors, let unexpected exceptions
  propagate to the global error handler.
- **Security:** Never inject unescaped user-supplied or API-sourced strings into HTML/SVG output.
  Use `html.escape()` for all such values.

---

## Submitting a PR

1. Fork the repo and create a feature branch: `git checkout -b feat/my-feature`.
2. Write or update tests for any changed behavior.
3. Make sure `pytest tests/` passes.
4. Open a pull request against `main` with a clear description of what changed and why.

---

## Filing Issues

- **Bug reports:** Include the GitHub username that triggered the issue (if public),
  the HTTP response you received, and the steps to reproduce.
- **Feature requests:** Describe the use case, not just the solution. Include mockups
  if relevant.

---

## Known Limitations

| Limitation | Notes |
|---|---|
| **In-memory cache** | The 5-minute TTL cache is per-process. On Vercel serverless, each cold start has an empty cache. For production scale, replace with Redis (e.g. Upstash). |
| **Contribution calendar scraping** | `_fetch_contribution_calendar` scrapes GitHub's HTML SVG. It has no rate limit protection and will silently fall back to the event-based heatmap if GitHub changes their markup. |
| **Social graph limited to 10** | The `followers` and `following` lists are capped at 10 per side (GitHub API default). The social graph reflects only those 10, not the full follower/following lists. |
| **Event window** | GitHub's public events API exposes at most 1,000 events (~10 pages × 100). Heatmap, streaks, and activity data are limited to this window. |
