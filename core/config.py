"""
core/config.py
==============
Configuration, environment variable loading, server tokens, and global constants.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

import httpx

BASE_DIR = Path(__file__).resolve().parent.parent

# Automatically load .env file if present
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    try:
        for _line in _env_path.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _k, _v = _k.strip(), _v.strip().strip("'\"")
                if _k and _v and (_k not in os.environ or not os.environ[_k].strip()):
                    os.environ[_k] = _v
    except Exception:
        pass


def _get_server_token() -> Optional[str]:
    """Return GITHUB_TOKEN from os.environ or re-read directly from .env."""
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and tok.strip():
        return tok.strip()
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k == "GITHUB_TOKEN" and v:
                        os.environ["GITHUB_TOKEN"] = v
                        return v
        except Exception:
            pass
    return None


logger = logging.getLogger("git-spectre")

# Allowed origins: production domain + localhost for dev.
_DEFAULT_ORIGINS = [
    "https://git-spectre.vercel.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]
_env_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: List[str] = (
    [o.strip() for o in _env_origins.split(",") if o.strip()]
    if _env_origins
    else _DEFAULT_ORIGINS
)

GITHUB_API = "https://api.github.com"
TIMEOUT = httpx.Timeout(28.0, connect=10.0)
MAX_RETRIES = 2
BACKOFF = 0.5  # seconds, doubles each retry

# Application version metadata (Single Source of Truth)
APP_VERSION = os.getenv("APP_VERSION", "3.1.1")
APP_VERSION_SHORT = "v" + ".".join(APP_VERSION.split(".")[:2])
APP_VERSION_MAJOR = "v" + APP_VERSION.split(".")[0]

# Official repository metadata
GITHUB_REPO = os.getenv("GITHUB_REPO", "chiragjaiswar0814/Git-Spectre")
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"

