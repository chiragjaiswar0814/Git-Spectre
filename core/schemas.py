"""
core/schemas.py
===============
Pydantic models, request validators, and validation regexes for input sanitation.
"""

from __future__ import annotations

import html as _html
import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]{0,37}[a-zA-Z0-9]$|^[a-zA-Z0-9]$")
# Matches classic GitHub PAT formats (ghp_, gho_, ghu_, ghr_, ghs_) and fine-grained PATs (github_pat_)
_TOKEN_RE = re.compile(r"^(?:gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{22,255})$")


def _validate_username(v: str) -> str:
    """Validate GitHub username according to GitHub naming rules."""
    v = v.strip()
    if not v:
        raise ValueError("Username cannot be empty.")
    if not _USERNAME_RE.match(v):
        raise ValueError(
            "Invalid GitHub username. Use only letters, numbers, and hyphens (1–39 chars)."
        )
    return v


def _validate_token(v: Optional[str]) -> Optional[str]:
    """Validate GitHub PAT format — rejects obviously invalid or injected strings."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if not _TOKEN_RE.match(v):
        raise ValueError(
            "Invalid GitHub token format. Provide a valid Personal Access Token "
            "(ghp_…, gho_…, ghu_…, ghr_…, or ghs_…)."
        )
    return v


class _WithToken(BaseModel):
    """Mixin that adds a validated, optional github_token field to all request models."""

    github_token: Optional[str] = None

    @field_validator("github_token")
    @classmethod
    def validate_token(cls, v: Optional[str]) -> Optional[str]:
        return _validate_token(v)


class AnalyzeRequest(_WithToken):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return _validate_username(v)


class CompareRequest(_WithToken):
    username_a: str
    username_b: str

    @field_validator("username_a", "username_b")
    @classmethod
    def validate_usernames(cls, v: str) -> str:
        return _validate_username(v)


class BatchRequest(_WithToken):
    usernames: List[str] = Field(..., min_length=1, max_length=10)

    @field_validator("usernames", mode="before")
    @classmethod
    def validate_usernames(cls, v: List[str]) -> List[str]:
        return [_validate_username(u) for u in v]


def _make_badge_svg(left: str, right: str, color: str) -> str:
    """Minimal shields.io-compatible flat SVG badge (delegates to core.badge)."""
    from core.badge import generate_pill_badge
    return generate_pill_badge(left=left, right=right, color=color, style="flat")

