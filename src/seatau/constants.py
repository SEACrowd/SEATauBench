"""Shared SEA-Tau paths and language registry constants."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import paths as path_defs


@lru_cache(maxsize=1)
def load_language_registry() -> dict[str, dict[str, str]]:
    """Load the canonical raw language registry."""
    return json.loads(
        path_defs.resolve_project_path(path_defs.LANGUAGES_PATH).read_text(
            encoding="utf-8"
        )
    )


def get_language_codes() -> tuple[str, ...]:
    """Return supported language codes in registry order."""
    return tuple(load_language_registry())


def get_language_display_name_by_code() -> dict[str, str]:
    """Return ``{language_code: display_name}`` from the language registry."""
    return {
        code: entry["display_name"] for code, entry in load_language_registry().items()
    }


def get_language_code_by_display_name() -> dict[str, str]:
    """Return ``{display_name: language_code}`` from the language registry."""
    return {
        display_name: code
        for code, display_name in get_language_display_name_by_code().items()
    }


def get_l2_language_codes() -> tuple[str, ...]:
    """Return supported non-English language codes in registry order."""
    return tuple(code for code in get_language_codes() if code != "en")


def to_project_relative_path(path: Path) -> Path:
    """Return ``path`` relative to the project root."""
    resolved = path_defs.resolve_project_path(path)
    try:
        return resolved.relative_to(path_defs.PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Path {resolved} is outside project root {path_defs.PROJECT_ROOT}"
        ) from exc


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root when needed."""
    return path_defs.resolve_project_path(path)


def get_domain_data_path(domain: str, lang_id: str | None = None) -> Path:
    """Return the data path for a domain or translated language subdirectory."""
    base = path_defs.resolve_project_path(path_defs.TAU2_DOMAINS_DATA) / domain
    if lang_id:
        return base / lang_id
    return base


def get_domain_src_path(domain: str) -> Path:
    """Return the source path for a domain."""
    return path_defs.resolve_project_path(path_defs.TAU2_DOMAINS_SRC) / domain


def path_matches(path: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Match a tuple path with ``*`` wildcard support."""
    if len(path) != len(pattern):
        return False
    for actual, expected in zip(path, pattern):
        if expected == "*":
            continue
        if actual != expected:
            return False
    return True


def matches_any(path: tuple[str, ...], patterns: tuple[tuple[str, ...], ...]) -> bool:
    """Return whether ``path`` matches at least one pattern."""
    return any(path_matches(path, pattern) for pattern in patterns)
