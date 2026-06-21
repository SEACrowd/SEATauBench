"""Generic text helpers used across SEA-Tau code."""

from __future__ import annotations


def squash(text: str, limit: int) -> str:
    """Single-line truncate text for audit CSVs."""
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else clean[: limit - 3].rstrip() + "..."
