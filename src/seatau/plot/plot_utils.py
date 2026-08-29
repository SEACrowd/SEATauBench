"""Matplotlib style setup and shared plot helpers."""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from paths import ANALYSES_DIR
from seatau.analysis import experiment_metrics as _experiment_metrics
from seatau.plot.config import (
    EXPORT_DPI,
    EXPORT_FORMATS,
    MODEL_ORDER,
    PLOT_BASE_FONT_SIZE,
    PLOT_FONT_FAMILY,
    PLOT_LABEL_SIZE,
    PLOT_LEGEND_SIZE,
    PLOT_TICK_SIZE,
    PLOT_TITLE_SIZE,
    SEA_COLORS,
)

matplotlib.use("Agg")

normalize_key_series = _experiment_metrics.normalize_key_series
normalize_scenario_id_series = _experiment_metrics.normalize_scenario_id_series
load_and_prepare = _experiment_metrics.load_and_prepare
experiment_language_metric_breakdown = (
    _experiment_metrics.experiment_language_metric_breakdown
)

LANGUAGE_PALETTE = {
    "EN": SEA_COLORS["black"],
    "ZH": SEA_COLORS["blue"],
    "ID": SEA_COLORS["yellow"],
    "TH": SEA_COLORS["red"],
    "VI": SEA_COLORS["blue"],
    "TL": SEA_COLORS["yellow"],
}

METRIC_PALETTE = {
    "pass@1": SEA_COLORS["blue"],
    "pass^2": SEA_COLORS["yellow"],
    "pass^3": SEA_COLORS["black"],
    "rho^3": SEA_COLORS["red"],
}

MODEL_PALETTE = dict(
    zip(
        MODEL_ORDER,
        [SEA_COLORS["blue"], SEA_COLORS["red"], SEA_COLORS["yellow"]],
    )
)
INTERACTION_RECAP_PATH = ANALYSES_DIR / "error_breakdown.csv"


def normalize_scenario_column(
    df: pd.DataFrame, column: str = "scenario"
) -> pd.DataFrame:
    """Return a copy with a scenario column normalized to canonical ids."""

    if column not in df.columns:
        return df
    out = df.copy()
    out[column] = normalize_scenario_id_series(out[column])
    return out


def read_interaction_recap(path: Path = INTERACTION_RECAP_PATH) -> pd.DataFrame:
    """Read the interaction/domain recap dataset."""

    df = pd.read_csv(path)
    if "language" in df.columns:
        df["language"] = normalize_key_series(df["language"])
    return df


def apply_style() -> None:
    """Apply publication-quality rcParams. Call once at script startup."""
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": EXPORT_DPI,
            "savefig.bbox": "tight",
            "savefig.facecolor": SEA_COLORS["white"],
            "font.family": PLOT_FONT_FAMILY,
            "font.size": PLOT_BASE_FONT_SIZE,
            "figure.facecolor": SEA_COLORS["white"],
            "axes.facecolor": SEA_COLORS["white"],
            "text.color": SEA_COLORS["black"],
            "axes.labelcolor": SEA_COLORS["black"],
            "axes.edgecolor": SEA_COLORS["black"],
            "xtick.color": SEA_COLORS["black"],
            "ytick.color": SEA_COLORS["black"],
            "axes.titlesize": PLOT_TITLE_SIZE,
            "axes.labelsize": PLOT_LABEL_SIZE,
            "xtick.labelsize": PLOT_TICK_SIZE,
            "ytick.labelsize": PLOT_TICK_SIZE,
            "legend.fontsize": PLOT_LEGEND_SIZE,
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
            "axes.linewidth": 0.7,
            "grid.linewidth": 0.45,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def despine(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def save_figure(
    fig: plt.Figure, name: str, fig_dir: Path, formats: tuple[str, ...] = EXPORT_FORMATS
) -> list[Path]:
    """Save fig to fig_dir/<name>.<ext> for each format.

    Args:
        fig: Matplotlib figure to save.
        name: Output filename stem (no extension).
        fig_dir: Directory to write into (created if missing).
        formats: Tuple of file extensions, e.g. ("pdf", "png", "svg").

    Returns:
        List of written paths.
    """
    fig_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for ext in formats:
        out = fig_dir / f"{name}.{ext}"
        fig.savefig(
            out,
            dpi=EXPORT_DPI,
            bbox_inches="tight",
            facecolor=SEA_COLORS["white"],
        )
        saved.append(out)
    print(f"Saved {name}:")
    for p in saved:
        print(f"  {p}")
    return saved
