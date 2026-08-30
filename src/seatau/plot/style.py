"""Shared palette, typography, and helpers for SEA-TauBench figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patheffects import withStroke

from paths import (
    ANALYSES_DIR,
    EXPERIMENTS_CSV,
    FIGS_DIR,
    PROJECT_ROOT,
)
from seatau.analysis import experiment_metrics as _experiment_metrics
from seatau.experiment_constants import (
    FILTER_SETTING,
    LANGUAGE_CODE_BY_KEY,
    LANGUAGE_DISPLAY_NAME_BY_CODE,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    METRIC_RENAMES,
    MODEL_LABELS,
    MODEL_ORDER,
    NON_BASELINE_SCENARIO_ORDER,
    PRIMARY_METRICS,
    SCENARIO_ID_BY_NAME,
    SCENARIO_LABELS,
    SCENARIO_NAME_BY_ID,
    SCENARIO_ORDER,
    TOOL_MIX_ORDER,
)

matplotlib.use("Agg")

__all__ = [
    "DEFAULT_CSV_PATH",
    "DEFAULT_FIG_DIR",
    "EXPORT_FORMATS",
    "FILTER_SETTING",
    "LANGUAGE_CODE_BY_KEY",
    "LANGUAGE_DISPLAY_NAME_BY_CODE",
    "LANGUAGE_DISPLAY_NAMES",
    "LANGUAGE_LABELS",
    "LANGUAGE_ORDER",
    "METRIC_LINESTYLES",
    "METRIC_PALETTE",
    "METRIC_RENAMES",
    "MODEL_LABELS",
    "MODEL_MARKERS",
    "MODEL_ORDER",
    "MODEL_PALETTE",
    "NON_BASELINE_SCENARIO_ORDER",
    "PLOT_BASE_FONT_SIZE",
    "PLOT_COLUMN_WIDTH",
    "PLOT_FIGSIZE_ONE_COL",
    "PLOT_FIGSIZE_ONE_COL_SHORT",
    "PLOT_FIGSIZE_ONE_COL_TALL",
    "PLOT_FIGSIZE_TWO_COL",
    "PLOT_FIGSIZE_TWO_COL_LARGE",
    "PLOT_FIGSIZE_TWO_COL_SHORT",
    "PLOT_FIGSIZE_TWO_COL_TALL",
    "PLOT_FIGSIZE_TWO_COL_WIDE",
    "PLOT_LABEL_SIZE",
    "PLOT_LEGEND_SIZE",
    "PLOT_PANEL_SIZE",
    "PLOT_TICK_SIZE",
    "PLOT_TITLE_SIZE",
    "PRIMARY_METRICS",
    "REPO_ROOT",
    "SCENARIO_ID_BY_NAME",
    "SCENARIO_LABELS",
    "SCENARIO_NAME_BY_ID",
    "SCENARIO_ORDER",
    "SEA_COLOR_SEQUENCE",
    "SEA_COLOR_SEQUENCE_6",
    "SEA_COLORS",
    "TOOL_MIX_ORDER",
    "annotated_cell_text_kwargs",
    "apply_style",
    "contrast_ratio",
    "contrasting_text_color",
    "despine",
    "experiment_language_metric_breakdown",
    "load_and_prepare",
    "normalize_key_series",
    "normalize_scenario_column",
    "normalize_scenario_id_series",
    "read_interaction_recap",
    "save_figure",
]


REPO_ROOT = PROJECT_ROOT
DEFAULT_CSV_PATH = EXPERIMENTS_CSV
DEFAULT_FIG_DIR = FIGS_DIR

EXPORT_FORMATS = ("pdf", "png")
EXPORT_DPI = 400

SEA_COLORS = {
    # Contrast- and color-vision-validated palette; black is reserved for text.
    "red": "#f50012",
    "blue": "#007aec",
    "yellow": "#e1a100",
    "green": "#008e5c",
    "purple": "#ac5fbe",
    "teal": "#00869c",
    "white": "#ffffff",
    "black": "#1a1a1a",
}
SEA_COLOR_SEQUENCE = (
    SEA_COLORS["blue"],
    SEA_COLORS["red"],
    SEA_COLORS["yellow"],
)
# Keep this order for six-category charts to maximize adjacent CVD separation.
SEA_COLOR_SEQUENCE_6 = (
    SEA_COLORS["green"],
    SEA_COLORS["blue"],
    SEA_COLORS["red"],
    SEA_COLORS["teal"],
    SEA_COLORS["yellow"],
    SEA_COLORS["purple"],
)


PLOT_FONT_FAMILY = ("Helvetica Neue", "Avenir Next", "DejaVu Sans")
PLOT_BASE_FONT_SIZE = 8
PLOT_TITLE_SIZE = 10
PLOT_LABEL_SIZE = 9
PLOT_TICK_SIZE = 8
PLOT_LEGEND_SIZE = 8
PLOT_COLUMN_WIDTH = 3.35
PLOT_TWO_COLUMN_WIDTH = 7.0
PLOT_ROW_HEIGHT = 2.5
PLOT_PANEL_SIZE = (2.55, 2.15)
PLOT_FIGSIZE_ONE_COL = (PLOT_COLUMN_WIDTH, 2.45)
PLOT_FIGSIZE_ONE_COL_TALL = (PLOT_COLUMN_WIDTH, 4.15)
PLOT_FIGSIZE_ONE_COL_SHORT = (PLOT_COLUMN_WIDTH, 1.85)
PLOT_FIGSIZE_TWO_COL = (PLOT_TWO_COLUMN_WIDTH, 2.95)
PLOT_FIGSIZE_TWO_COL_SHORT = (PLOT_TWO_COLUMN_WIDTH, 2.2)
PLOT_FIGSIZE_TWO_COL_TALL = (PLOT_TWO_COLUMN_WIDTH, 4.4)
PLOT_FIGSIZE_TWO_COL_LARGE = (PLOT_TWO_COLUMN_WIDTH, 6.0)
PLOT_FIGSIZE_TWO_COL_WIDE = (8.8, 4.4)

# Re-export shared experiment constants and metric helpers for plot callers.

normalize_key_series = _experiment_metrics.normalize_key_series
normalize_scenario_id_series = _experiment_metrics.normalize_scenario_id_series
load_and_prepare = _experiment_metrics.load_and_prepare
experiment_language_metric_breakdown = (
    _experiment_metrics.experiment_language_metric_breakdown
)

# Language colors follow LANGUAGE_ORDER and the fixed six-color sequence.
LANGUAGE_PALETTE = {
    "EN": SEA_COLORS["green"],
    "TH": SEA_COLORS["blue"],
    "VI": SEA_COLORS["red"],
    "ID": SEA_COLORS["teal"],
    "ZH": SEA_COLORS["yellow"],
    "TL": SEA_COLORS["purple"],
}

METRIC_PALETTE = {
    "pass@1": SEA_COLORS["blue"],
    "pass^2": SEA_COLORS["yellow"],
    "pass^3": SEA_COLORS["green"],
    "rho^3": SEA_COLORS["red"],
}

MODEL_PALETTE = dict(
    zip(
        MODEL_ORDER,
        [SEA_COLORS["blue"], SEA_COLORS["red"], SEA_COLORS["yellow"]],
    )
)
MODEL_MARKERS = dict(zip(MODEL_ORDER, ("o", "s", "^"), strict=True))
METRIC_LINESTYLES = {"pass@1": "-", "pass^2": "--", "pass^3": ":", "rho^3": "-."}
INTERACTION_RECAP_PATH = ANALYSES_DIR / "error_breakdown.csv"


def relative_luminance(color: str | tuple[float, float, float]) -> float:
    """Return the WCAG relative luminance of a Matplotlib color."""

    rgb = matplotlib.colors.to_rgb(color)
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in rgb
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(
    foreground: str | tuple[float, float, float],
    background: str | tuple[float, float, float],
) -> float:
    """Return the WCAG 2 contrast ratio for two colors."""

    foreground_lum = relative_luminance(foreground)
    background_lum = relative_luminance(background)
    lighter, darker = (
        max(foreground_lum, background_lum),
        min(foreground_lum, background_lum),
    )
    return (lighter + 0.05) / (darker + 0.05)


def contrasting_text_color(
    background: str | tuple[float, float, float, float] | tuple[float, float, float],
) -> str:
    """Choose the higher-contrast black or white text for a background."""

    candidates = (SEA_COLORS["black"], SEA_COLORS["white"])
    return max(candidates, key=lambda text: contrast_ratio(text, background))


def annotated_cell_text_kwargs(
    background: str | tuple[float, float, float, float] | tuple[float, float, float],
    *,
    linewidth: float = 2.0,
) -> dict:
    """Return text color and optional halo kwargs for a colored cell.

    Use a halo only when neither black nor white reaches 4.5:1 contrast.
    """

    text_color = contrasting_text_color(background)
    if contrast_ratio(text_color, background) >= 4.5:
        return {"color": text_color}

    halo_color = (
        SEA_COLORS["white"]
        if text_color == SEA_COLORS["black"]
        else SEA_COLORS["black"]
    )
    return {
        "color": text_color,
        "path_effects": [withStroke(linewidth=linewidth, foreground=halo_color)],
    }


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
