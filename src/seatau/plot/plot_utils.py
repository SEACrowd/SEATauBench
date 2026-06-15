"""Matplotlib style setup and shared plot helpers."""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

from seatau.plot.config import EXPORT_DPI, EXPORT_FORMATS, MODEL_ORDER

matplotlib.use("Agg")

OKABE_ITO = {
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
    "black": "#000000",
}

LANGUAGE_PALETTE = {
    "EN": OKABE_ITO["orange"],
    "ZH": OKABE_ITO["sky_blue"],
    "ID": OKABE_ITO["blue"],
    "TH": OKABE_ITO["bluish_green"],
    "VI": OKABE_ITO["reddish_purple"],
    "TL": OKABE_ITO["vermillion"],
}

METRIC_PALETTE = {
    "pass@1": OKABE_ITO["sky_blue"],
    "pass@2": OKABE_ITO["bluish_green"],
    "pass@3": OKABE_ITO["vermillion"],
    "rho^3": OKABE_ITO["vermillion"],
}

MODEL_PALETTE = dict(
    zip(
        MODEL_ORDER,
        [
            OKABE_ITO["orange"],
            OKABE_ITO["sky_blue"],
            OKABE_ITO["bluish_green"],
            OKABE_ITO["reddish_purple"],
        ],
    )
)


def apply_style() -> None:
    """Apply publication-quality rcParams. Call once at script startup."""
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": EXPORT_DPI,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
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


def save_figure(fig: plt.Figure, name: str, fig_dir: Path, formats: tuple[str, ...] = EXPORT_FORMATS) -> list[Path]:
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
        fig.savefig(out, dpi=EXPORT_DPI, bbox_inches="tight", facecolor="white")
        saved.append(out)
    print(f"Saved {name}:")
    for p in saved:
        print(f"  {p}")
    return saved
