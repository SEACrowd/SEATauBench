"""Shared path constants for the SEA-TAU package."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DATA_DIR = Path("data")
SRC_DIR = Path("src")
SEATAU_DIR = SRC_DIR / "seatau"
SEATAU_DATA_DIR = PROJECT_DATA_DIR / "seatau"
ANALYSES_DIR = PROJECT_DATA_DIR / "analyses"
FIGS_DIR = Path("figs")

LANGUAGES_PATH = SEATAU_DATA_DIR / "languages.json"
SCENARIOS_PATH = SEATAU_DATA_DIR / "scenarios.yaml"
L2_TOOLS_MIX_DIR = SEATAU_DIR / "l2_tools_mix"

ANNOTATION_MANIFEST_DIR = SEATAU_DATA_DIR / "annotations"
EXPERIMENTS_CSV = SEATAU_DATA_DIR / "experiments.csv"
EXPERIMENT_LANGUAGE_SUMMARY_CSV = ANALYSES_DIR / "experiment_language_summary.csv"
PERF_BY_LANGUAGE_CSV = ANALYSES_DIR / "perf_by_language.csv"
EN_VS_L2_PERF_CSV = ANALYSES_DIR / "en_vs_l2_perf.csv"
METRIC_CORRELATIONS_BY_LANGUAGE_CSV = (
    ANALYSES_DIR / "metric_correlations_by_language.csv"
)
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

TAU2_DOMAINS_DATA = PROJECT_DATA_DIR / "tau2" / "domains"
TAU2_DOMAINS_SRC = SRC_DIR / "tau2" / "domains"

DEFAULT_FASTTEXT_LID_MODEL_PATH = PROJECT_DATA_DIR / "models" / "lid.176.bin"
DEFAULT_FASTTEXT_LID_COMPRESSED_MODEL_PATH = PROJECT_DATA_DIR / "models" / "lid.176.ftz"


def resolve_project_path(path: str | Path) -> Path:
    """Resolve a project-relative path against ``PROJECT_ROOT``."""
    path = Path(path)
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def resolve_runtime_data_dir() -> Path:
    """Resolve tau2 runtime data root, respecting ``TAU2_DATA_DIR``."""
    data_dir = os.getenv("TAU2_DATA_DIR")
    if data_dir:
        return Path(data_dir).expanduser().resolve()
    return resolve_project_path(PROJECT_DATA_DIR)


def path_label(path: str | Path) -> str:
    """Return a stable project-relative path string for help text."""
    return Path(path).as_posix()
