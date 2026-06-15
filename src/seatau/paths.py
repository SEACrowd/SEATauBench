"""Canonical filesystem paths and path utilities for the SEA-TAU package."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"

SEATAU_DIR = Path(__file__).resolve().parent
LANGUAGES_PATH = SEATAU_DIR / "languages.json"
EXPERIMENTS_YAML = SEATAU_DIR / "experiments.yaml"
MIXED_LANG_TOOLS_DIR = SEATAU_DIR / "mixed_lang_tools"

ANNOTATION_MANIFEST_DIR = DATA_DIR / "seatau" / "annotation"
EXPERIMENTS_CSV = DATA_DIR / "seatau" / "experiments.csv"

TAU2_DOMAINS_DATA = DATA_DIR / "tau2" / "domains"
TAU2_DOMAINS_SRC = SRC_DIR / "tau2" / "domains"


def to_project_relative_path(path: Path) -> Path:
    """Return ``path`` relative to the project root.

    Args:
        path: Any path (absolute or relative).

    Returns:
        Path relative to PROJECT_ROOT.

    Raises:
        ValueError: If path is outside the project root.
    """
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Path {resolved} is outside project root {PROJECT_ROOT}"
        ) from exc


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root when needed.

    Args:
        path: Absolute path or project-relative path.

    Returns:
        Resolved absolute path.
    """
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved.resolve()
    return (PROJECT_ROOT / resolved).resolve()


def get_domain_data_path(domain: str, lang_id: str | None = None) -> Path:
    """Get the data path for a domain, optionally with language subdirectory.

    Args:
        domain: Domain name (e.g., "airline", "retail").
        lang_id: Optional language code (e.g., "th", "vi").

    Returns:
        Path to domain data directory or language subdirectory.
    """
    base = TAU2_DOMAINS_DATA / domain
    if lang_id:
        return base / lang_id
    return base


def get_domain_src_path(domain: str) -> Path:
    """Get the source path for a domain.

    Args:
        domain: Domain name (e.g., "airline", "retail").

    Returns:
        Path to domain source directory.
    """
    return TAU2_DOMAINS_SRC / domain


def path_matches(path: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Match a tuple path with '*' wildcard support.

    Args:
        path: Tuple of path segments to match.
        pattern: Tuple of pattern segments, may include '*' wildcards.

    Returns:
        True if path matches pattern.
    """
    if len(path) != len(pattern):
        return False
    for actual, expected in zip(path, pattern):
        if expected == "*":
            continue
        if actual != expected:
            return False
    return True


def matches_any(path: tuple[str, ...], patterns: tuple[tuple[str, ...], ...]) -> bool:
    """Check if path matches any of the given patterns.

    Args:
        path: Tuple of path segments to match.
        patterns: Tuple of patterns to check against.

    Returns:
        True if path matches at least one pattern.
    """
    return any(path_matches(path, pattern) for pattern in patterns)
