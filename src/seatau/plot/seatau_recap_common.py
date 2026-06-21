"""Shared inputs and helpers for SEA-Tau recap figures."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from seatau.plot.config import DEFAULT_FIG_DIR, REPO_ROOT

DEFAULT_ANALYSIS_DIR = REPO_ROOT / "data" / "analyses"
RECAP_PATH = DEFAULT_ANALYSIS_DIR / "recap_v2.csv"
RECAP_BREAKDOWN_PATH = DEFAULT_ANALYSIS_DIR / "recap_breakdown.csv"

LANGUAGES = ["English", "Filipino", "Vietnamese", "Indonesian", "Thai", "Chinese"]
LANGUAGE_LABELS = {
    "English": "EN",
    "Vietnamese": "VI",
    "Thai": "TH",
    "Indonesian": "ID",
    "Chinese": "ZH",
    "Filipino": "TL",
}
MODEL_LABELS = {
    "qwen3-235b-a22b-inst": "Qwen3-235B Inst",
    "gpt-5-mini": "GPT-5 Mini",
    "kimi-k2.5": "Kimi K2.5",
    "qwen3.6-35b-a3b": "Qwen3.6-35B A3B",
}
MODEL_COLORS = {
    "gpt-5-mini": "#0072B2",
    "qwen3-235b-a22b-inst": "#D55E00",
    "kimi-k2.5": "#009E73",
    "qwen3.6-35b-a3b": "#CC79A7",
}

VALID_FORMATS = ("png", "pdf", "both")


def add_format_args(parser: argparse.ArgumentParser) -> None:
    """Add common output arguments to a figure script parser."""

    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument(
        "--format",
        choices=VALID_FORMATS,
        default="png",
        help="Output format. Use 'both' to write PNG and PDF.",
    )


def output_formats(format_name: str) -> tuple[str, ...]:
    """Normalize a CLI format option into file extensions."""

    if format_name == "both":
        return ("png", "pdf")
    return (format_name,)


def save_figure(
    fig: plt.Figure,
    stem: str,
    output_dir: Path,
    format_name: str,
    dpi: int = 300,
) -> list[Path]:
    """Save a figure in the requested format(s)."""

    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for ext in output_formats(format_name):
        path = output_dir / f"{stem}.{ext}"
        fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
        saved.append(path)
    plt.close(fig)
    return saved


def read_recap(path: Path = RECAP_PATH) -> pd.DataFrame:
    """Read the interaction/domain recap dataset."""

    return pd.read_csv(path)


def read_recap_breakdown(path: Path = RECAP_BREAKDOWN_PATH) -> pd.DataFrame:
    """Read the per-domain, per-model performance recap dataset."""

    return pd.read_csv(path)


def recap_breakdown_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows used by the notebook's performance summary figures."""

    return df.loc[
        df["Model"].ne("qwen3.6-35b-a3b") & ~df["Metric"].isin(["pass^2", "pass^3"]),
        :,
    ].copy()
