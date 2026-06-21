"""Plot pass@1 and rho^3 by language as model-level radar charts."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from seatau.plot.plot_utils import apply_style
from seatau.plot.seatau_recap_common import (
    LANGUAGE_LABELS,
    LANGUAGES,
    MODEL_COLORS,
    MODEL_LABELS,
    RECAP_BREAKDOWN_PATH,
    add_format_args,
    read_recap_breakdown,
    recap_breakdown_metrics,
    save_figure,
)

FIGURE_STEM = "pass1_rho3_by_language"


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the pass@1/rho^3 radar chart from recap breakdown rows."""

    radar_df = (
        recap_breakdown_metrics(df)
        .groupby(["Metric", "Model"], as_index=False)[LANGUAGES]
        .mean()
    )
    metrics = radar_df["Metric"].unique()
    fig, axes = plt.subplots(
        1,
        len(metrics),
        subplot_kw={"polar": True},
        figsize=(5 * len(metrics), 6),
    )
    if len(metrics) == 1:
        axes = [axes]

    angles = np.linspace(0, 2 * np.pi, len(LANGUAGES), endpoint=False).tolist()
    angles += angles[:1]
    for ax, metric in zip(axes, metrics, strict=True):
        sub = radar_df.loc[radar_df["Metric"].eq(metric)]
        for _, row in sub.iterrows():
            model = row["Model"]
            values = row[LANGUAGES].tolist()
            values += values[:1]
            color = MODEL_COLORS.get(model, "#333333")
            ax.plot(angles, values, linewidth=6, color=color, alpha=0.18, zorder=2)
            ax.plot(
                angles,
                values,
                linewidth=2.5,
                color=color,
                label=MODEL_LABELS.get(model, model),
                marker="o",
                markersize=2,
                markerfacecolor="white",
                markeredgewidth=1.2,
                zorder=3,
            )
            ax.fill(angles, values, alpha=0.08, color=color, zorder=1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([LANGUAGE_LABELS[lang] for lang in LANGUAGES])
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
        fontsize=15,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--breakdown", type=Path, default=RECAP_BREAKDOWN_PATH)
    add_format_args(parser)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    outputs = save_figure(
        build_figure(read_recap_breakdown(args.breakdown)),
        FIGURE_STEM,
        args.output_dir,
        args.format,
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
