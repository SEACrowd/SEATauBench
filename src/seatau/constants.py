"""Shared SEA-Tau paths and language registry constants."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
ANALYSES_DIR = DATA_DIR / "analyses"
FIGS_DIR = PROJECT_ROOT / "figs"

SEATAU_DIR = Path(__file__).resolve().parent
LANGUAGES_PATH = SEATAU_DIR / "languages.json"
SCENARIOS_MAP = SEATAU_DIR / "scenarios.yaml"
MIXED_LANG_TOOLS_DIR = SEATAU_DIR / "mixed_lang_tools"

ANNOTATION_MANIFEST_DIR = DATA_DIR / "seatau" / "annotation"
EXPERIMENTS_CSV = DATA_DIR / "seatau" / "experiments.csv"
EXPERIMENT_LANGUAGE_SUMMARY_CSV = ANALYSES_DIR / "experiment_language_summary.csv"
LANGUAGE_DRIFT_SUMMARY_DIR = ANALYSES_DIR / "language_drift_summary"
LANGUAGE_DRIFT_DIAGNOSTICS_DIR = ANALYSES_DIR / "language_drift_diagnostics"
LANGUAGE_DRIFT_RUN_SUMMARY_CSV = (
    LANGUAGE_DRIFT_DIAGNOSTICS_DIR / "contextual_run_language.csv"
)
LANGUAGE_DRIFT_TURN_POSITION_CSV = (
    LANGUAGE_DRIFT_DIAGNOSTICS_DIR / "contextual_turn_position.csv"
)
LANGUAGE_DRIFT_TOOL_MIX_SUMMARY_CSV = (
    LANGUAGE_DRIFT_DIAGNOSTICS_DIR / "contextual_tool_mix_summary.csv"
)
FAILURE_MODE_DIR = ANALYSES_DIR / "failure_mode"

TAU2_DOMAINS_DATA = DATA_DIR / "tau2" / "domains"
TAU2_DOMAINS_SRC = SRC_DIR / "tau2" / "domains"

DEFAULT_FASTTEXT_LID_MODEL_PATH = DATA_DIR / "models" / "lid.176.bin"
DEFAULT_FASTTEXT_LID_COMPRESSED_MODEL_PATH = DATA_DIR / "models" / "lid.176.ftz"

LANGUAGE_REGISTRY: dict[str, dict[str, str]] = json.loads(
    LANGUAGES_PATH.read_text(encoding="utf-8")
)
LANGUAGE_CODES = tuple(LANGUAGE_REGISTRY)
LANGUAGE_DISPLAY_NAME_BY_CODE = {
    code: entry["display_name"] for code, entry in LANGUAGE_REGISTRY.items()
}
LANGUAGE_CODE_BY_DISPLAY_NAME = {
    display_name: code for code, display_name in LANGUAGE_DISPLAY_NAME_BY_CODE.items()
}
L2_LANGUAGE_CODES = tuple(code for code in LANGUAGE_CODES if code != "en")


def to_project_relative_path(path: Path) -> Path:
    """Return ``path`` relative to the project root."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Path {resolved} is outside project root {PROJECT_ROOT}"
        ) from exc


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a path relative to the project root when needed."""
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved.resolve()
    return (PROJECT_ROOT / resolved).resolve()


def get_domain_data_path(domain: str, lang_id: str | None = None) -> Path:
    """Return the data path for a domain or translated language subdirectory."""
    base = TAU2_DOMAINS_DATA / domain
    if lang_id:
        return base / lang_id
    return base


def get_domain_src_path(domain: str) -> Path:
    """Return the source path for a domain."""
    return TAU2_DOMAINS_SRC / domain


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
