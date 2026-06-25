"""Plot English scores against average non-English scores by domain."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from paths import ANALYSES_DIR, EXPERIMENTS_CSV
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    PLOT_TWO_COLUMN_WIDTH,
    SEA_COLORS,
)
from seatau.plot.data import (
    DEFAULT_BOOTSTRAP_SAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    build_en_vs_l2_perf_data,
)
from seatau.plot.plot_utils import (
    MODEL_PALETTE,
    apply_style,
    despine,
    save_figure,
)

FIGURE_STEM = "en_vs_l2_perf"
FIGURE_WIDTH = PLOT_TWO_COLUMN_WIDTH * 0.4 / 0.58
FIGURE_HEIGHT = 3.7
METRIC_LABEL_SIZE = 16
TICK_SIZE = 13
DOMAIN_LABEL_SIZE = 13
KEY_SIZE = 11
MARKER_SIZE = 7.0
DEFAULT_RUN_UNCERTAINTY_CSV = ANALYSES_DIR / "statistical_rigor" / "run_uncertainty.csv"


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the English versus non-English dumbbell chart.

    Each domain/model pair is a connected pair of markers: an open marker at the
    non-English mean and a filled marker at the English score, joined by a line
    whose length is the English/non-English gap. The metric names sit on the
    y-axis and model colors are read from the adjacent perf_by_language legend,
    so only the non-English/English marker key is drawn here.
    """

    plot_df = df.copy()
    domains = plot_df["domain"].unique()
    metrics = plot_df["metric"].unique()
    preferred_domain_order = ["Retail", "Airline", "Telecom"]
    domain_order = [d for d in preferred_domain_order if d in domains]
    domain_order += [d for d in domains if d not in domain_order]
    models = list(plot_df["model"].unique())
    max_val = np.nanmax(
        np.r_[
            plot_df["english_ci_high"].to_numpy(dtype=float),
            plot_df["non_english_ci_high"].to_numpy(dtype=float),
        ]
    )
    xmax = min(1.0, max_val * 1.08)

    fig = plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))
    grid = fig.add_gridspec(len(metrics), 1, hspace=0.12)
    axes = [fig.add_subplot(grid[idx, 0]) for idx in range(len(metrics))]

    y_base = np.arange(len(domain_order))
    offsets = (
        np.linspace(-0.26, 0.26, len(models)) if len(models) > 1 else np.array([0.0])
    )
    for idx, (ax, metric) in enumerate(zip(axes, metrics, strict=True)):
        for k in range(len(domain_order)):
            if k % 2 == 0:
                ax.axhspan(
                    k - 0.5,
                    k + 0.5,
                    color=SEA_COLORS["black"],
                    alpha=0.05,
                    zorder=0,
                )
        for j, model in enumerate(models):
            color = MODEL_PALETTE.get(model, SEA_COLORS["black"])
            sub = (
                plot_df.loc[plot_df["metric"].eq(metric) & plot_df["model"].eq(model)]
                .set_index("domain")
                .reindex(domain_order)
            )
            en_vals = sub["english_estimate"].to_numpy(dtype=float)
            non_en_vals = sub["non_english_estimate"].to_numpy(dtype=float)
            y = y_base + offsets[j]
            ax.hlines(
                y,
                non_en_vals,
                en_vals,
                color=color,
                lw=2.2,
                alpha=0.75,
                zorder=2,
            )
            ax.plot(
                non_en_vals,
                y,
                marker="o",
                linestyle="none",
                markersize=MARKER_SIZE,
                markerfacecolor=SEA_COLORS["white"],
                markeredgecolor=color,
                markeredgewidth=1.6,
                zorder=4,
            )
            ax.plot(
                en_vals,
                y,
                marker="o",
                linestyle="none",
                markersize=MARKER_SIZE,
                markerfacecolor=color,
                markeredgecolor=SEA_COLORS["black"],
                markeredgewidth=0.6,
                zorder=4,
            )
        ax.set_xlim(0.0, xmax)
        ax.set_ylim(-0.6, len(domain_order) - 0.4)
        ax.set_yticks(y_base)
        ax.set_yticklabels(domain_order, fontsize=DOMAIN_LABEL_SIZE)
        ax.set_ylabel(
            "$" + metric.replace("rho", "\\rho") + "$",
            fontsize=METRIC_LABEL_SIZE,
            labelpad=8,
        )
        ax.grid(axis="x", alpha=0.4)
        ax.set_axisbelow(True)
        despine(ax)
        ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _pos: f"{x:.0%}"))
        ax.tick_params(axis="x", labelsize=TICK_SIZE)
        if idx != len(metrics) - 1:
            ax.tick_params(axis="x", labelbottom=False)

    _draw_endpoint_key(fig)
    fig.subplots_adjust(left=0.20, right=0.97, top=0.97, bottom=0.17)
    return fig


def _draw_endpoint_key(fig: plt.Figure) -> None:
    """Draw the ``Non-English mean ◦——● English mean`` marker key at the bottom."""

    key_ax = fig.add_axes((0.0, 0.0, 1.0, 0.08))
    key_ax.axis("off")
    key_ax.set_xlim(0, 1)
    key_ax.set_ylim(0, 1)
    open_x, fill_x, y = 0.45, 0.55, 0.5
    key_ax.plot([open_x, fill_x], [y, y], color=SEA_COLORS["black"], lw=1.8, zorder=1)
    key_ax.plot(
        open_x,
        y,
        marker="o",
        markersize=MARKER_SIZE,
        markerfacecolor=SEA_COLORS["white"],
        markeredgecolor=SEA_COLORS["black"],
        markeredgewidth=1.6,
        zorder=2,
    )
    key_ax.plot(
        fill_x,
        y,
        marker="o",
        markersize=MARKER_SIZE,
        markerfacecolor=SEA_COLORS["black"],
        markeredgecolor=SEA_COLORS["black"],
        markeredgewidth=0.6,
        zorder=2,
    )
    key_ax.text(
        open_x - 0.02,
        y,
        "Non-English mean",
        ha="right",
        va="center",
        fontsize=KEY_SIZE,
    )
    key_ax.text(
        fill_x + 0.02,
        y,
        "English mean",
        ha="left",
        va="center",
        fontsize=KEY_SIZE,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=EXPERIMENTS_CSV)
    parser.add_argument(
        "--run-uncertainty-csv",
        type=Path,
        default=DEFAULT_RUN_UNCERTAINTY_CSV,
        help="Optional run-level uncertainty CSV for English task-bootstrap CIs.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    df = build_en_vs_l2_perf_data(
        args.experiments_csv,
        run_uncertainty_csv=args.run_uncertainty_csv,
        bootstraps=args.bootstraps,
        seed=args.seed,
    )
    outputs = save_figure(
        build_figure(df),
        FIGURE_STEM,
        args.output_dir,
        tuple(args.formats),
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
