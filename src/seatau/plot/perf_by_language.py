"""Plot pass@1 and rho^3 by language as model-level radar charts."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import EXPERIMENTS_CSV
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    MODEL_LABELS,
    PLOT_TWO_COLUMN_WIDTH,
    SEA_COLORS,
)
from seatau.plot.data import (
    DEFAULT_BOOTSTRAP_SAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    build_perf_by_language_data,
)
from seatau.plot.plot_utils import (
    MODEL_PALETTE,
    apply_style,
    save_figure,
)

FIGURE_STEM = "perf_by_language"
TITLE_SIZE = 16
TICK_SIZE = 13
RADIAL_TICK_SIZE = 11
LEGEND_SIZE = 13


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the pass@1/rho^3 radar chart from recap breakdown rows."""

    metrics = df["metric"].unique()
    fig = plt.figure(figsize=(PLOT_TWO_COLUMN_WIDTH, 3.45))
    grid = fig.add_gridspec(
        2,
        len(metrics),
        height_ratios=[1.0, 0.12],
        hspace=0.15,
        wspace=0.15,
    )
    axes = [
        fig.add_subplot(grid[0, idx], projection="polar") for idx in range(len(metrics))
    ]

    angles = np.linspace(0, 2 * np.pi, len(LANGUAGE_ORDER), endpoint=False).tolist()
    angles += angles[:1]
    for ax, metric in zip(axes, metrics, strict=True):
        sub = df.loc[df["metric"].eq(metric)]
        for model, model_df in sub.groupby("model", sort=False):
            indexed = model_df.set_index("language").reindex(LANGUAGE_ORDER)
            values = indexed["estimate"].to_numpy(dtype=float)
            closed_values = values.tolist() + values[:1].tolist()
            color = MODEL_PALETTE.get(model, SEA_COLORS["black"])
            ax.plot(
                angles,
                closed_values,
                linewidth=6,
                color=color,
                alpha=0.18,
                zorder=2,
            )
            ax.plot(
                angles,
                closed_values,
                linewidth=2.8,
                color=color,
                label=MODEL_LABELS.get(model, model),
                marker="o",
                markersize=2.8,
                markerfacecolor=SEA_COLORS["white"],
                markeredgewidth=1.2,
                zorder=3,
            )
            ax.fill(angles, closed_values, alpha=0.07, color=color, zorder=1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(
            [LANGUAGE_LABELS[lang] for lang in LANGUAGE_ORDER],
            fontsize=TICK_SIZE,
        )
        ax.set_ylim(0, 0.81)
        ax.set_title(
            "$" + metric.replace("rho", "\\rho") + "$",
            pad=14,
            fontsize=TITLE_SIZE,
        )
        ax.set_yticks([0.2, 0.4, 0.6, 0.8])
        ax.set_yticklabels(["20%", "40%", "60%", "80%"], fontsize=RADIAL_TICK_SIZE)
        ax.grid(True, alpha=1.0)

    handles, labels = axes[0].get_legend_handles_labels()
    legend_ax = fig.add_subplot(grid[1, :])
    legend_ax.axis("off")
    legend_ax.legend(
        handles,
        labels,
        loc="center",
        ncol=len(labels),
        fontsize=LEGEND_SIZE,
        frameon=True,
        fancybox=True,
        borderpad=0.4,
        handlelength=2.5,
        columnspacing=1.6,
    )
    fig.subplots_adjust(left=0.03, right=0.98, top=0.92, bottom=0.09)
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=EXPERIMENTS_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    df = build_perf_by_language_data(
        args.experiments_csv,
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
