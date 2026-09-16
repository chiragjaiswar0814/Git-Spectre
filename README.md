# Git-Spectre 👁️ — Developer Deep-Profiler & GitHub Analytics Engine

![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![AsyncIO](https://img.shields.io/badge/AsyncIO-Python%203.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?style=flat-square&logo=chartdotjs&logoColor=white)
![GitHub REST API](https://img.shields.io/badge/GitHub%20REST%20API-v3-181717?style=flat-square&logo=github&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)](https://git-spectre.vercel.app/)
![Version](https://img.shields.io/badge/version-2.1-22d3ee?style=flat-square)

> 🚀 **[https://git-spectre.vercel.app/](https://git-spectre.vercel.app/)** — live, no setup required.

---

## Why I Built This

I read a lot of resumes. Most of them are, frankly, identical — two pages of bullet points claiming proficiency in frameworks the candidate has used once on a tutorial project. The standard black-and-white resume tells me very little about how someone actually codes.

The manual alternative is worse: I open their GitHub profile, click through a dozen repos, try to piece together what languages they actually *use* versus what they list on their CV, and after ten minutes I still don't have a clear picture. It's tedious work that doesn't need to be.

So I built **Git-Spectre** — a "Threat Intel"-style dossier generator for any public GitHub user. Drop in a username **or paste a full GitHub profile URL** and within seconds you get a visual breakdown of their real language distribution, a calculated **Developer Archetype**, commit quality analysis, community activity, and their top projects by impact. A 10-minute manual process becomes a 10-second automated one.

---

## What's in v2.1

### ✨ New Features

| Feature | Description |
|---|---|
| **GitHub URL Input** | Paste `https://github.com/username` directly — extracts the handle automatically |
| **Search History** | Last 10 scans saved in `localStorage`, shown as a dropdown with avatars on focus |
| **Commit Message Quality** | Rates 0–100: vague-commit %, avg length, best & worst message |
| **Community Activity Panel** | PR open/merge counts, issues, comments, external repo pushes |
| **Fork Analysis Panel** | Original vs forked ratio with per-card health indicators |
| **Repo Health Badges** | 🟢 Active / 🟡 Stale / 🔴 Archived on each repo card |
| **Chronotype Badge** | 🦉 Night Owl / 🐦 Early Bird / ⚡ Midday Coder / 🌆 Evening Dev |
| **Radar Dual-View** | Toggle language radar between KB (code volume) and # (repo count) |
| **Shareable PNG Card** | Download a 600×315 dark profile card as a PNG image |
| **Shareable URL** | URL updates to `/?u={username}` — share or bookmark any profile |
| **Batch Screener** | Rank up to 10 profiles concurrently by Dev Score™ in a leaderboard |
| **Embed Widget** | `GET /embed/{username}` → self-contained HTML card for READMEs & iframes |
| **Keyboard Shortcuts** | `Ctrl+K` search · `Ctrl+E` PDF · `Ctrl+D` compare · `Ctrl+B` batch · `Ctrl+T` theme |
| **Dark / Light Mode** | One-click toggle, preference saved to `localStorage` |
| **Rate-Limit Countdown** | Live API gauge; `MM:SS` countdown when below 25% remaining |

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

On top of that, repo fetching fans out across **3 pages concurrently** (up to 300 repos). The result is that a user with 150+ repositories takes roughly the same wall-clock time to scan as one with 10.

All HTTP calls go through **`httpx.AsyncClient`** with configurable timeouts and an **exponential back-off retry loop** on transient network errors.

---

## Bring Your Own Key (BYOK)

Git-Spectre works **without any API key** out of the box. GitHub's unauthenticated REST API allows **60 requests/hour**, which is enough for a quick profile scan.

For heavy use — interviewing candidates back-to-back or running the batch screener — that limit gets hit fast. That's where the built-in **API Vault** comes in.

The frontend includes a local API key input that stores your **GitHub Personal Access Token (PAT)** directly in `localStorage`. It never touches a server. When a token is present, it's attached as a `Bearer` header on every outbound request, bumping the limit to **5,000 requests/hour**.

```
No token    →   60  req/hour  (good for casual use)
With PAT    →  5000 req/hour  (good for bulk screening)
```

To generate a token: [GitHub → Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens). You only need **public read** scope.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | FastAPI + Uvicorn | Async-native, auto-generates API docs at `/docs` |
| **HTTP Client** | `httpx.AsyncClient` | Drop-in async replacement for `requests`; native `asyncio` support |
| **Frontend** | Vanilla JS + TailwindCSS (CDN) | No build step, no bundler, ships as a single `index.html` |
| **Charts** | Chart.js 4.x | Radar, bar, stacked-bar charts — no heavy dependencies |
| **Export** | html2canvas + jsPDF | Client-side PDF + PNG card generation |
| **GitHub Data** | GitHub REST API v3 | Public, no SDK needed |
| **Hosting** | Vercel (`@vercel/python`) | Serverless FastAPI — zero infrastructure |

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
uvicorn main:app --reload
```

The server starts on **`http://localhost:8000`**.

- **UI** → `http://localhost:8000/`
- **API docs** → `http://localhost:8000/docs`

Optionally, set a default token via environment variable:

```bash
# Windows (PowerShell)
$env:GITHUB_TOKEN = "ghp_your_token_here"

# macOS / Linux
GITHUB_TOKEN=ghp_your_token_here uvicorn main:app --reload
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + K` | Focus search bar |
| `Ctrl + E` | Export PDF |
| `Ctrl + D` | Open Compare modal |
| `Ctrl + B` | Open Batch Screener |
| `Ctrl + T` | Toggle dark / light mode |
| `Esc` | Close any open modal |

---

## Deploy to Vercel

This repo is pre-configured for Vercel via [`vercel.json`](./vercel.json) and [`requirements.txt`](./requirements.txt).

### One-click deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/chiragjaiswar0814/Git-Spectre)

### Manual deploy

```bash
npm i -g vercel
vercel
```

### Optional: set a default GitHub token on Vercel

In the Vercel dashboard → **Project → Settings → Environment Variables**, add:

```
GITHUB_TOKEN = ghp_your_token_here
```

---

## API Reference

### `POST /api/analyze`

Accepts a username or is called after URL extraction on the frontend.

```json
{
  "username": "torvalds",
  "github_token": "ghp_optional"
}
```

**Response includes:**

| Field | Description |
|---|---|
| `profile` | Name, bio, location, company, followers, blog |
| `stats` | Total stars, own repos, forked repos |
| `languages` | `{lang: bytes}` map across all owned repos |
| `lang_repo_counts` | `{lang: repo_count}` — for radar dual-view |
| `archetype` | Label, glow colour, description |
| `score` | Total (0–1000), grade (S+→E), breakdown by category |
| `heatmap` | `{"YYYY-MM-DD": commit_count}` for last 91 days |
| `activity_hours` | 7×24 grid of event counts (Mon–Sun × 0–23h UTC) |
| `streaks` | Current streak, longest streak, total active days |
| `top_repos` | Top repos by stars with full metadata |
| `community` | PRs opened/merged, issues, comments, external repos |
| `commit_messages` | First lines of up to 200 recent commits |
| `fork_details` | Forked repos sorted by stars |
| `gists` | Total gists, most forked, top language |
| `topics` | Aggregated repo topic tag counts |
| `lang_evolution` | `{year: {lang: bytes}}` — stack evolution chart |
| `orgs` | Organisation membership |
| `followers_list` | First 30 followers with avatars |
| `following_list` | First 30 following with avatars |

---

### `POST /api/compare`

Compare two profiles side-by-side.

```json
{
  "username_a": "torvalds",
  "username_b": "gvanrossum",
  "github_token": "ghp_optional"
}
```

Returns `{ "user_a": <full dossier>, "user_b": <full dossier> }`.

---

### `POST /api/batch`

Rank up to 10 profiles concurrently by Dev Score™.

```json
{
  "usernames": ["torvalds", "gvanrossum", "antirez"],
  "github_token": "ghp_optional"
}
```

Returns a sorted array of summary objects (score, grade, archetype, top language, stars, followers).

---

### `GET /embed/{username}`

Returns a self-contained dark HTML card (~2KB). Embed in any HTML page:

```html
<iframe src="https://git-spectre.vercel.app/embed/torvalds"
        width="340" height="220" frameborder="0"></iframe>
```

---

### `GET /api/rate-limit`

Returns current GitHub API quota:

```json
{ "limit": 60, "remaining": 54, "reset": 1726499400, "used": 6 }
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

## Dev Score™ Breakdown

The score runs from 0 to 1,000 and is computed from six weighted signals:

| Signal | Max Points |
|---|---|
| Total stars across owned repos | 300 |
| Follower count | 200 |
| Language diversity | 150 |
| Own repo count | 100 |
| Account tenure | 80 |
| Recent activity (events) | 70 |

Grades: **S+** (900+) · **S** (750+) · **A** (600+) · **B** (450+) · **C** (300+) · **D** (150+) · **E** (<150)

---

## License

MIT © [Chirag Jaiswar](https://github.com/chiragjaiswar0814) — see [`LICENSE`](./LICENSE) for details.
