"""
core/badge.py
=============
Dynamic SVG Generator for GitHub Profile READMEs & Embeds.
Produces lightweight, GitHub Camo-compatible vector graphics:
- Compact Shields-style Pill Badges (Flat, Cyber, For-The-Badge)
- Rich Tactical Dossier Profile Cards (GitHub README stats style)
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional, Tuple

# Grade accent colors matching Git-Spectre theme system
GRADE_COLORS: Dict[str, str] = {
    "S+": "#f59e0b",
    "S": "#10b981",
    "A": "#06b6d4",
    "B": "#8b5cf6",
    "C": "#f97316",
    "D": "#ef4444",
    "E": "#6b7280",
}

# Curated theme definitions
THEMES: Dict[str, Dict[str, str]] = {
    "spectre": {
        "bg_start": "#090d16",
        "bg_end": "#0f172a",
        "card_bg": "#0b0f19",
        "border": "#1e293b",
        "divider": "#1e293b",
        "title": "#f8fafc",
        "text": "#94a3b8",
        "muted": "#64748b",
        "accent": "#10b981",
        "accent_glow": "#22d3ee",
        "role_color": "#38bdf8",
        "star_color": "#f59e0b",
        "card_bar_bg": "rgba(255, 255, 255, 0.08)",
        "pill_left_bg": "#1e293b",
    },
    "dark": {
        "bg_start": "#0d1117",
        "bg_end": "#161b22",
        "card_bg": "#0d1117",
        "border": "#30363d",
        "divider": "#30363d",
        "title": "#f0f6fc",
        "text": "#8b949e",
        "muted": "#6e7681",
        "accent": "#58a6ff",
        "accent_glow": "#1f6feb",
        "role_color": "#58a6ff",
        "star_color": "#f59e0b",
        "card_bar_bg": "rgba(255, 255, 255, 0.08)",
        "pill_left_bg": "#21262d",
    },
    "tokyo": {
        "bg_start": "#1a1b26",
        "bg_end": "#16161e",
        "card_bg": "#16161e",
        "border": "#2f3549",
        "divider": "#2f3549",
        "title": "#c0caf5",
        "text": "#9aa5ce",
        "muted": "#565f89",
        "accent": "#bb9af7",
        "accent_glow": "#7dcfff",
        "role_color": "#7dcfff",
        "star_color": "#e0af68",
        "card_bar_bg": "rgba(255, 255, 255, 0.1)",
        "pill_left_bg": "#24283b",
    },
    "matrix": {
        "bg_start": "#030a05",
        "bg_end": "#051308",
        "card_bg": "#030a05",
        "border": "#133e1a",
        "divider": "#133e1a",
        "title": "#4ade80",
        "text": "#22c55e",
        "muted": "#166534",
        "accent": "#22c55e",
        "accent_glow": "#86efac",
        "role_color": "#86efac",
        "star_color": "#4ade80",
        "card_bar_bg": "rgba(34, 197, 94, 0.15)",
        "pill_left_bg": "#09230e",
    },
    "light": {
        "bg_start": "#ffffff",
        "bg_end": "#f8fafc",
        "card_bg": "#ffffff",
        "border": "#e2e8f0",
        "divider": "#e2e8f0",
        "title": "#0f172a",
        "text": "#475569",
        "muted": "#94a3b8",
        "accent": "#0284c7",
        "accent_glow": "#0ea5e9",
        "role_color": "#0284c7",
        "star_color": "#d97706",
        "card_bar_bg": "rgba(0, 0, 0, 0.06)",
        "pill_left_bg": "#e2e8f0",
    },
}

# Recognized language color map (GitHub standard)
LANG_COLORS: Dict[str, str] = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Rust": "#dea584",
    "Go": "#00ADD8",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Java": "#b07219",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Shell": "#89e051",
    "Bash": "#89e051",
    "Vue": "#41b883",
    "React": "#61dafb",
    "Svelte": "#ff3e00",
    "Lua": "#000080",
    "Zig": "#ec915c",
    "Elixir": "#6e4a7e",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "Julia": "#a270ba",
    "Haskell": "#5e5086",
    "Clojure": "#db5855",
    "Dockerfile": "#384d54",
}


def _get_lang_color(lang: str) -> str:
    """Return specific language color or deterministic HSL fallback."""
    if lang in LANG_COLORS:
        return LANG_COLORS[lang]
    h = 0
    for char in lang:
        h = ord(char) + ((h << 5) - h)
    hue = abs(h) % 360
    return f"hsl({hue}, 68%, 60%)"


def _compact_number(n: Any) -> str:
    """Format numbers into compact strings (e.g. 1.2k, 3.4M)."""
    try:
        num = float(n)
    except (ValueError, TypeError):
        return "0"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}".rstrip("0").rstrip(".") + "k"
    return str(int(num))


# ============================================================================
# 1. COMPACT PILL BADGE GENERATOR
# ============================================================================

def generate_pill_badge(
    left: str,
    right: str,
    color: str = "#10b981",
    style: str = "flat",
    theme: str = "spectre",
) -> str:
    """Generate a clean, high-precision SVG pill badge (Shields.io / Cyber).

    Supports:
    - style="flat": Classic shields style with rounded corners (rx="3")
    - style="cyber": Git-Spectre tactical style with glowing border
    - style="for-the-badge": Chunky tall badge (height 28)
    """
    th = THEMES.get(theme.lower(), THEMES["spectre"])
    left_str = str(left).strip()
    right_str = str(right).strip()

    left_e = html.escape(left_str, quote=True)
    right_e = html.escape(right_str, quote=True)
    color_e = html.escape(color, quote=True)

    if style == "for-the-badge":
        height = 28
        font_size = 11
        letter_spacing = 1.0
        left_upper = left_e.upper()
        right_upper = right_e.upper()
        lw = int(len(left_upper) * 7.5 + 24)
        rw = int(len(right_upper) * 7.5 + 24)
        total = lw + rw
        lx = lw / 2
        rx = lw + (rw / 2)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height}" role="img" aria-label="{left_e}: {right_e}">
  <title>{left_e}: {right_e}</title>
  <clipPath id="r"><rect width="{total}" height="{height}" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{lw}" height="{height}" fill="{th['pill_left_bg']}"/>
    <rect x="{lw}" width="{rw}" height="{height}" fill="{color_e}"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif" font-size="{font_size}" font-weight="700" letter-spacing="{letter_spacing}">
    <text x="{lx}" y="18" fill="#fff">{left_upper}</text>
    <text x="{rx}" y="18" fill="#fff">{right_upper}</text>
  </g>
</svg>"""

    elif style == "cyber":
        height = 24
        font_size = 11
        lw = int(len(left_str) * 6.8 + 20)
        rw = int(len(right_str) * 6.8 + 20)
        total = lw + rw
        lx = lw / 2 + 5
        rx = lw + (rw / 2)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height}" role="img" aria-label="{left_e}: {right_e}">
  <title>{left_e}: {right_e}</title>
  <defs>
    <linearGradient id="cyber-bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{th['bg_start']}"/>
      <stop offset="100%" stop-color="{th['bg_end']}"/>
    </linearGradient>
  </defs>
  <rect width="{total}" height="{height}" rx="5" fill="url(#cyber-bg)" stroke="{th['border']}" stroke-width="1"/>
  <!-- Status dot -->
  <circle cx="10" cy="12" r="3" fill="{color_e}"/>
  <!-- Divider -->
  <line x1="{lw}" y1="4" x2="{lw}" y2="20" stroke="{th['border']}" stroke-width="1"/>
  <g text-anchor="middle" font-family="'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace" font-size="{font_size}">
    <text x="{lx}" y="16" fill="{th['title']}" font-weight="600">{left_e}</text>
    <text x="{rx}" y="16" fill="{color_e}" font-weight="700">{right_e}</text>
  </g>
</svg>"""

    else:
        # Default flat shields.io style
        height = 20
        lw = int(len(left_str) * 6.5 + 16)
        rw = int(len(right_str) * 6.5 + 16)
        total = lw + rw
        lx = lw / 2
        rx = lw + (rw / 2)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{height}" role="img" aria-label="{left_e}: {right_e}">
  <title>{left_e}: {right_e}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".15"/>
    <stop offset="100%" stop-color="#000" stop-opacity=".2"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total}" height="{height}" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{lw}" height="{height}" fill="{th['pill_left_bg']}"/>
    <rect x="{lw}" width="{rw}" height="{height}" fill="{color_e}"/>
    <rect width="{total}" height="{height}" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,sans-serif" font-size="11" font-weight="600">
    <text x="{lx}" y="15" fill="#010101" fill-opacity=".3">{left_e}</text>
    <text x="{lx}" y="14" fill="#fff">{left_e}</text>
    <text x="{rx}" y="15" fill="#010101" fill-opacity=".3">{right_e}</text>
    <text x="{rx}" y="14" fill="#fff">{right_e}</text>
  </g>
</svg>"""


# ============================================================================
# 2. SLEEK DEVELOPER PROFILE BADGE GENERATOR
# ============================================================================

def _format_role(archetype: Optional[Dict[str, Any]]) -> str:
    """Format developer archetype into a natural, professional title."""
    if not archetype:
        return "Full-Stack Developer"
    raw = str(archetype.get("title") or archetype.get("label") or "Full-Stack Developer").strip()
    upper_raw = raw.upper()
    if upper_raw in ("CODE CRAFTSMAN", "THE GENERALIST"):
        return "Full-Stack Developer"
    if upper_raw == "THE POLYGLOT":
        return "Polyglot Engineer"
    if upper_raw.endswith(" SPECIALIST"):
        prefix = raw[:-len(" SPECIALIST")].strip()
        subwords = "-".join(sub.capitalize() for sub in prefix.split("-"))
        return f"{subwords} Specialist"
    words = []
    for w in raw.split():
        if w.lower() in ("in", "of", "and", "the"):
            words.append(w.lower())
        else:
            words.append("-".join(sub.capitalize() for sub in w.split("-")))
    return " ".join(words)


def _format_stars(total_stars: int) -> str:
    """Format stars with commas (e.g. 1,284) or clean compact suffix."""
    if total_stars >= 1_000_000:
        return f"{total_stars / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if total_stars >= 10_000:
        return f"{total_stars / 1_000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{total_stars:,}"


def _get_top_language(languages: Optional[Dict[str, int]]) -> str:
    """Return the developer's primary programming language."""
    if not languages:
        return "Developer"
    items = list(languages.items())
    if not items:
        return "Developer"
    return max(items, key=lambda x: x[1])[0]


def _get_initials(name_or_login: str) -> str:
    """Extract 1-2 letter initials for fallback vector avatar."""
    parts = name_or_login.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif parts and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    elif parts and len(parts[0]) == 1:
        return parts[0][0].upper()
    return "GS"


def generate_profile_badge(
    profile: Dict[str, Any],
    score: Dict[str, Any],
    archetype: Optional[Dict[str, Any]] = None,
    languages: Optional[Dict[str, int]] = None,
    total_stars: int = 0,
    avatar_b64: Optional[str] = None,
    theme: str = "spectre",
    border: bool = True,
    avatar_pos: str = "name",
    rank_info: Optional[Dict[str, Any]] = None,
    streaks: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a clean, high-end developer pill badge matching the reference design:
    [ ★ 1,284 | (Avatar) Zur Rinubi  Full-Stack Developer | 9,850 XP | TypeScript ]

    Parameters:
    - profile: Dict containing user profile ('login', 'name', 'avatar_url', etc.)
    - score: Dict containing score ('total', 'tier', etc.)
    - archetype: Archetype classification info
    - languages: Language byte counts dictionary
    - total_stars: Earned stargazers count
    - avatar_b64: Optional base64-encoded avatar data URI
    - theme: Theme key ('spectre', 'dark', 'tokyo', 'matrix', 'light')
    - border: Whether to render subtle border stroke
    - avatar_pos: 'name' (next to name), 'left' (far left), or 'none'
    """
    th = THEMES.get(theme.lower(), THEMES["spectre"])
    star_color = th.get("star_color", "#f59e0b")
    divider_color = th.get("divider", th["border"])
    role_color = th.get("role_color", th.get("accent_glow", "#38bdf8"))
    stroke_attr = f'stroke="{th["border"]}" stroke-width="1"' if border else ""

    login = str(profile.get("login") or "developer").strip()
    name = str(profile.get("name") or "").strip()
    display_name = name if name else login

    stars_count = int(total_stars or profile.get("stars_earned", 0))
    stars_str = _format_stars(stars_count)

    role_text = _format_role(archetype)
    score_total = int(score.get("total", 0))
    xp_str = f"{score_total:,} XP"

    top_lang = _get_top_language(languages)
    lang_color = _get_lang_color(top_lang)

    display_name_e = html.escape(display_name, quote=True)
    role_e = html.escape(role_text, quote=True)
    stars_e = html.escape(stars_str, quote=True)
    xp_e = html.escape(xp_str, quote=True)
    lang_e = html.escape(top_lang, quote=True)
    initials_e = html.escape(_get_initials(display_name), quote=True)

    has_avatar = avatar_pos in ("name", "left")

    x = 20.0
    av_markup = ""
    av_cx = None
    div0_markup = ""

    clean_id = re.sub(r'[^a-zA-Z0-9]', '', login)
    clip_id = f"av-clip-{clean_id}" if clean_id else "av-clip-user"

    if has_avatar and avatar_pos == "left":
        av_cx = x + 14.0
        x = av_cx + 14.0 + 12.0
        div0_x = x
        div0_markup = f'<line x1="{div0_x:.1f}" y1="12" x2="{div0_x:.1f}" y2="34" stroke="{divider_color}" stroke-width="1"/>'
        x += 16.0

    star_icon_x = x
    star_text_x = star_icon_x + 18.0
    star_w = 18.0 + len(stars_str) * 7.8
    x = star_icon_x + star_w
    div1_x = x + 16.0
    x = div1_x + 16.0

    if has_avatar and avatar_pos == "name":
        av_cx = x + 14.0
        x = av_cx + 14.0 + 10.0

    name_x = x
    name_w = len(display_name) * 8.2
    role_x = name_x + name_w + 10.0
    role_w = len(role_text) * 7.0
    x = role_x + role_w
    div2_x = x + 16.0
    x = div2_x + 16.0

    xp_x = x
    xp_w = len(xp_str) * 7.8
    x = xp_x + xp_w
    div3_x = x + 16.0
    x = div3_x + 16.0

    lang_x = x
    lang_w = len(top_lang) * 7.6
    total_w = int(lang_x + lang_w + 20.0)

    title_color = th["title"]

    # Avatar element markup
    if has_avatar and av_cx is not None:
        if avatar_b64:
            avatar_href = avatar_b64 if avatar_b64.startswith("data:") else f"data:image/png;base64,{avatar_b64}"
            av_content = f'<image href="{avatar_href}" x="{av_cx - 14.0:.1f}" y="9" width="28" height="28" clip-path="url(#{clip_id})" preserveAspectRatio="xMidYMid slice"/>'
        else:
            av_content = f'<text x="{av_cx:.1f}" y="27" font-size="11" font-weight="700" fill="{title_color}" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif">{initials_e}</text>'

        av_markup = f"""  <defs>
    <clipPath id="{clip_id}"><circle cx="{av_cx:.1f}" cy="23" r="14"/></clipPath>
  </defs>
  <circle cx="{av_cx:.1f}" cy="23" r="14" fill="{th.get('card_bar_bg', 'rgba(255,255,255,0.08)')}" stroke="{divider_color}" stroke-width="1"/>
  {av_content}
  <circle cx="{av_cx:.1f}" cy="23" r="14" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="1"/>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="46" viewBox="0 0 {total_w} 46" role="img" aria-label="Git-Spectre Profile: {display_name_e}">
  <title>Git-Spectre: {display_name_e} ({role_e}) | {xp_e} | {lang_e}</title>
  <style>
    .bold {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 700; }}
    .med {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 500; }}
    .semi {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 600; }}
  </style>

  <!-- Card Background -->
  <rect width="{total_w}" height="46" rx="12" fill="{th.get('card_bg', th['bg_start'])}" {stroke_attr}/>

  <!-- Avatar -->
{av_markup}
  {div0_markup}

  <!-- Star Section -->
  <g transform="translate({star_icon_x:.1f}, 16)">
    <path d="M6.5 1l1.7 3.5 3.8.5-2.8 2.7.7 3.8-3.4-1.8-3.4 1.8.7-3.8-2.8-2.7 3.8-.5z" fill="{star_color}"/>
  </g>
  <text x="{star_text_x:.1f}" y="27" font-size="13.5" fill="{star_color}" class="bold">{stars_e}</text>

  <!-- Divider 1 -->
  <line x1="{div1_x:.1f}" y1="12" x2="{div1_x:.1f}" y2="34" stroke="{divider_color}" stroke-width="1"/>

  <!-- Developer Identity -->
  <text x="{name_x:.1f}" y="27" font-size="14" fill="{th['title']}" class="bold">{display_name_e}</text>
  <text x="{role_x:.1f}" y="27" font-size="13" fill="{role_color}" class="med">{role_e}</text>

  <!-- Divider 2 -->
  <line x1="{div2_x:.1f}" y1="12" x2="{div2_x:.1f}" y2="34" stroke="{divider_color}" stroke-width="1"/>

  <!-- Dev Score XP -->
  <text x="{xp_x:.1f}" y="27" font-size="13.5" fill="{th['title']}" class="semi">{xp_e}</text>

  <!-- Divider 3 -->
  <line x1="{div3_x:.1f}" y1="12" x2="{div3_x:.1f}" y2="34" stroke="{divider_color}" stroke-width="1"/>

  <!-- Primary Language -->
  <text x="{lang_x:.1f}" y="27" font-size="13.5" fill="{lang_color}" class="semi">{lang_e}</text>
</svg>"""


def generate_dossier_card(
    profile: Dict[str, Any],
    score: Dict[str, Any],
    archetype: Optional[Dict[str, Any]] = None,
    languages: Optional[Dict[str, int]] = None,
    rank_info: Optional[Dict[str, Any]] = None,
    streaks: Optional[Dict[str, Any]] = None,
    total_stars: int = 0,
    theme: str = "spectre",
    border: bool = True,
    avatar_b64: Optional[str] = None,
    avatar_pos: str = "name",
) -> str:
    """Developer Profile Badge generator (compatible alias for generate_profile_badge)."""
    return generate_profile_badge(
        profile=profile,
        score=score,
        archetype=archetype,
        languages=languages,
        total_stars=total_stars,
        avatar_b64=avatar_b64,
        theme=theme,
        border=border,
        avatar_pos=avatar_pos,
        rank_info=rank_info,
        streaks=streaks,
    )


# ============================================================================
# 3. ERROR / NOT FOUND BADGE
# ============================================================================

def generate_not_found_badge(username: str, style: str = "pill", theme: str = "spectre") -> str:
    """Generate a clean, graceful error badge when profile is not found."""
    if style == "card":
        th = THEMES.get(theme.lower(), THEMES["spectre"])
        u_e = html.escape(username, quote=True)
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="380" height="46" viewBox="0 0 380 46" role="img" aria-label="Git-Spectre: User Not Found">
  <rect width="380" height="46" rx="12" fill="{th.get('card_bg', th['bg_start'])}" stroke="{th['border']}" stroke-width="1"/>
  <circle cx="25" cy="23" r="12" fill="#ef4444" fill-opacity="0.15"/>
  <text x="25" y="27" fill="#ef4444" font-size="13" font-weight="bold" text-anchor="middle" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">!</text>
  <line x1="48" y1="12" x2="48" y2="34" stroke="{th.get('divider', th['border'])}" stroke-width="1"/>
  <text x="62" y="27" fill="{th['title']}" font-size="13.5" font-weight="600" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">User Not Found: @{u_e}</text>
  <line x1="260" y1="12" x2="260" y2="34" stroke="{th.get('divider', th['border'])}" stroke-width="1"/>
  <text x="276" y="27" fill="{th['accent']}" font-size="12" font-weight="600" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">git-spectre</text>
</svg>"""
    return generate_pill_badge("Git-Spectre", "not found", "#6b7280", style=style, theme=theme)
