"""Shared path constants for the SEA-TAU package."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
SEATAU_DIR = SRC_DIR / "seatau"

LANGUAGES_PATH = SEATAU_DIR / "languages.json"
EXPERIMENTS_PATH = SEATAU_DIR / "experiments.yaml"
MIXED_LANG_TOOLS_DIR = SEATAU_DIR / "mixed_lang_tools"
ANNOTATION_MANIFEST_DIR = DATA_DIR / "seatau" / "annotation"
