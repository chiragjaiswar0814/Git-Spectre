# Git-Spectre 👁️ — Developer Profiler & GitHub Analytics Engine

![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![AsyncIO](https://img.shields.io/badge/AsyncIO-Python%203.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?style=flat-square&logo=chartdotjs&logoColor=white)
![GitHub REST API](https://img.shields.io/badge/GitHub%20REST%20API-v3-181717?style=flat-square&logo=github&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)](https://git-spectre.vercel.app/)

> 🚀 **[https://git-spectre.vercel.app/](https://git-spectre.vercel.app/)** — live, no setup required.

---

## Why I Built This

I read a lot of resumes. Most of them are, frankly, identical — two pages of bullet points claiming proficiency in frameworks the candidate has used once on a tutorial project. The standard black-and-white resume tells me very little about how someone actually codes.

The manual alternative is worse: I open their GitHub profile, click through a dozen repos, try to piece together what languages they actually *use* versus what they list on their CV, and after ten minutes I still don't have a clear picture. It's tedious work that doesn't need to be.

So I built **Git-Spectre** — a "Threat Intel"-style dossier generator for any public GitHub user. I drop in a username and within seconds I get a visual breakdown of their real language distribution across all public repos, a calculated **Developer Archetype** label, and their top projects by impact. It turns a boring 10-minute manual process into a 10-second automated one.

---

## Core Engineering — Asynchronous GitHub Scraping

The performance of Git-Spectre is entirely dependent on how aggressively it hits the GitHub REST API in parallel. A naive synchronous approach would chain requests one after another: fetch the profile, *wait*, then fetch repos, *wait*, and so on. That's slow and pointless when the requests are independent of each other.

Instead, the backend uses **`asyncio.gather()`** to fire concurrent requests simultaneously from a single async context:

```python
# All 7 requests fire simultaneously — not queued
profile, repos, events, orgs, gists, followers, following = await asyncio.gather(
    _fetch_profile(client, username, headers),
    _fetch_repos(client, username, headers),
    _fetch_events(client, username, headers),
    _fetch_orgs(client, username, headers),
    _fetch_gists(client, username, headers),
    _fetch_followers(client, username, headers),
    _fetch_following(client, username, headers),
)
```

On top of that, repo fetching itself fans out across **3 pages concurrently** (up to 300 repos), each page request firing in parallel rather than sequentially. The result is that a user with 150+ repositories takes roughly the same wall-clock time to scan as one with 10.

All HTTP calls go through **`httpx.AsyncClient`** with configurable timeouts and an **exponential back-off retry loop** on transient network errors — so a single flaky connection doesn't crash the whole request.

---

## Bring Your Own Key (BYOK)

Git-Spectre works **without any API key** out of the box. GitHub's unauthenticated REST API allows **60 requests/hour**, which is enough for a quick profile scan.

For heavy use — interviewing a batch of candidates back-to-back, or running repeated scans — that limit gets hit fast. That's where the built-in **API Vault** comes in.

The frontend includes a local API key input that stores your **GitHub Personal Access Token (PAT)** directly in the browser's `localStorage`. It never touches a server. When a token is present, it's attached as a `Bearer` header on every outbound request, which bumps the limit to **5,000 requests/hour**.

```
No token    →   60  req/hour  (good for casual use)
With PAT    →  5000 req/hour  (good for bulk screening)
```

To generate a token: [GitHub → Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens). You only need **public read** scope — no write permissions required.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | FastAPI + Uvicorn | Async-native, minimal boilerplate, auto-generates API docs at `/docs` |
| **HTTP Client** | `httpx.AsyncClient` | Drop-in async replacement for `requests`; works natively with `asyncio` |
| **Frontend** | Vanilla JS + TailwindCSS | No build step, no bundler, ships as a single `index.html` |
| **Charts** | Chart.js | Radar and doughnut charts for language distribution — no heavy dependencies |
| **GitHub Data** | GitHub REST API v3 | Public, no SDK needed, raw `httpx` calls keep the dependency count low |
| **Hosting** | Vercel (`@vercel/python`) | Serverless FastAPI deployment — zero infrastructure to manage |

---

## Quick Start (Local)

**Prerequisites:** Python 3.11+

```bash
# 1. Clone the repo
git clone https://github.com/chiragjaiswar0814/Git-Spectre.git
cd Git-Spectre

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the backend
python main.py
```

The server starts on **`http://localhost:8000`**.

- **UI** → `http://localhost:8000/`
- **API docs** → `http://localhost:8000/docs`

Optionally, set a default token via environment variable so you don't have to enter it in the UI every time:

```bash
# Windows (PowerShell)
$env:GITHUB_TOKEN = "ghp_your_token_here"
python main.py

# macOS / Linux
GITHUB_TOKEN=ghp_your_token_here python main.py
```

---

## Deploy to Vercel

This repo is pre-configured for Vercel via [`vercel.json`](./vercel.json) and [`requirements.txt`](./requirements.txt).

### One-click deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/chiragjaiswar0814/Git-Spectre)

### Manual deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from the project root
vercel
```

### Optional: set a default GitHub token on Vercel

In the Vercel dashboard → **Project → Settings → Environment Variables**, add:

```
GITHUB_TOKEN = ghp_your_token_here
```

This makes the deployed app use an authenticated token by default (5,000 req/hr), without requiring users to enter one in the UI.

---

## API Reference

### `POST /api/analyze`

```json
{
  "username": "chiragjaiswar0814",
  "github_token": "ghp_optional_token"
}
```

Returns a structured dossier:

```json
{
  "profile":        { "login": "chiragjaiswar0814", "followers": 2, "public_repos": 81, "..." },
  "stats":          { "total_stars": 1, "own_repos": 72, "forked_repos": 9 },
  "languages":      { "Python": 182400, "JavaScript": 43200, "..." },
  "archetype":      { "label": "THE POLYGLOT", "glow": "#06b6d4", "description": "..." },
  "score":          { "total": 286, "grade": "D", "breakdown": { "stars": 0, "..." } },
  "heatmap":        { "2026-09-14": 3, "2026-09-15": 5 },
  "streaks":        { "current": 2, "longest": 7, "total_active_days": 45 },
  "top_repos":      [ { "name": "Git-Spectre", "stars": 1, "language": "Python", "url": "..." } ],
  "followers_list": [ { "login": "...", "avatar_url": "...", "url": "..." } ],
  "following_list": [ { "login": "...", "avatar_url": "...", "url": "..." } ],
  "gists":          { "total": 0, "top_language": null }
}
```

---

## Developer Archetypes

The archetype engine scores a user across followers, total stars, language diversity, and dominant-language concentration, then assigns one of the following labels:

| Archetype | Trigger Condition |
|---|---|
| `OPEN-SOURCE LEGEND` | 1,000+ total stars across own repos |
| `COMMUNITY BEACON` | 500+ followers |
| `THE POLYGLOT` | 8+ distinct languages used |
| `[LANG] SPECIALIST` | Single language accounts for 80%+ of code |
| `THE GENERALIST` | 5–7 languages in active use |
| `RISING STAR` | 100–999 total stars |
| `CODE CRAFTSMAN` | Everything else — building quietly |

---


