"""Plot pass@1 and rho^3 by language as model-level radar charts."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from seatau.plot.config import (
    DEFAULT_CSV_PATH,
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    MODEL_LABELS,
    PLOT_TITLE_SIZE,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    MODEL_PALETTE,
    apply_style,
    experiment_language_metric_breakdown,
    load_and_prepare,
    save_figure,
)

FIGURE_STEM = "perf_by_language"


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the pass@1/rho^3 radar chart from recap breakdown rows."""

    radar_df = df.groupby(["Metric", "Model"], as_index=False)[LANGUAGE_ORDER].mean()
    metrics = radar_df["Metric"].unique()
    fig, axes = plt.subplots(
        1,
        len(metrics),
        subplot_kw={"polar": True},
        figsize=(5 * len(metrics), 6),
    )
    if len(metrics) == 1:
        axes = [axes]

    angles = np.linspace(0, 2 * np.pi, len(LANGUAGE_ORDER), endpoint=False).tolist()
    angles += angles[:1]
    for ax, metric in zip(axes, metrics, strict=True):
        sub = radar_df.loc[radar_df["Metric"].eq(metric)]
        for _, row in sub.iterrows():
            model = row["Model"]
            values = row[LANGUAGE_ORDER].tolist()
            values += values[:1]
            color = MODEL_PALETTE.get(model, SEA_COLORS["black"])
            ax.plot(angles, values, linewidth=6, color=color, alpha=0.18, zorder=2)
            ax.plot(
                angles,
                values,
                linewidth=2.5,
                color=color,
                label=MODEL_LABELS.get(model, model),
                marker="o",
                markersize=2,
                markerfacecolor=SEA_COLORS["white"],
                markeredgewidth=1.2,
                zorder=3,
            )
            ax.fill(angles, values, alpha=0.08, color=color, zorder=1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([LANGUAGE_LABELS[lang] for lang in LANGUAGE_ORDER])
        ax.set_ylim(0, 0.81)
        ax.set_title("$" + metric.replace("rho", "\\rho") + "$", pad=20)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8])
        ax.set_yticklabels(["20%", "40%", "60%", "80%"])
        ax.grid(True, alpha=1.0)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower left",
        bbox_to_anchor=(0.33, 0.05),
        ncol=len(labels),
        fontsize=PLOT_TITLE_SIZE,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    _, _, clean_df, _, _ = load_and_prepare(args.csv)
    outputs = save_figure(
        build_figure(experiment_language_metric_breakdown(clean_df)),
        FIGURE_STEM,
        args.output_dir,
        tuple(args.formats),
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
