"""Diverging bar chart of English versus non-English scores by domain."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from paths import EN_VS_L2_PERF_CSV
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    MODEL_LABELS,
    PLOT_ROW_HEIGHT,
    PLOT_TWO_COLUMN_WIDTH,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    MODEL_PALETTE,
    apply_style,
    save_figure,
)

FIGURE_STEM = "en_vs_l2_perf_bars"
TITLE_SIZE = 15
TICK_SIZE = 12
DOMAIN_LABEL_SIZE = 12
SIDE_LABEL_SIZE = 13


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the diverging English versus non-English bar chart with 95% CIs."""

    plot_df = df.copy()
    domains = plot_df["domain"].unique()
    metrics = plot_df["metric"].unique()
    preferred_domain_order = ["Retail", "Airline", "Telecom"]
    domain_order = [d for d in preferred_domain_order if d in domains]
    domain_order += [d for d in domains if d not in domain_order]
    models = plot_df["model"].unique()
    max_val = np.nanmax(
        np.r_[
            plot_df["english_ci_high"].to_numpy(dtype=float),
            plot_df["non_english_ci_high"].to_numpy(dtype=float),
        ]
    )
    xmax = min(1.0, max_val * 1.15)

    fig, axes = plt.subplots(
        len(metrics),
        1,
        figsize=(PLOT_TWO_COLUMN_WIDTH, PLOT_ROW_HEIGHT * len(metrics)),
        squeeze=False,
    )
    y_base = np.arange(len(domain_order))
    offsets = (
        np.linspace(-0.22, 0.22, len(models)) if len(models) > 1 else np.array([0.0])
    )
    for i, metric in enumerate(metrics):
        ax = axes[i, 0]
        for j, model in enumerate(models):
            sub = (
                plot_df.loc[plot_df["metric"].eq(metric) & plot_df["model"].eq(model)]
                .set_index("domain")
                .reindex(domain_order)
            )
            en_vals = sub["english_estimate"].to_numpy(dtype=float)
            en_low = sub["english_ci_low"].to_numpy(dtype=float)
            en_high = sub["english_ci_high"].to_numpy(dtype=float)
            non_en_vals = sub["non_english_estimate"].to_numpy(dtype=float)
            non_en_low = sub["non_english_ci_low"].to_numpy(dtype=float)
            non_en_high = sub["non_english_ci_high"].to_numpy(dtype=float)
            y = y_base + offsets[j]
            bar_h = 0.18
            ax.barh(
                y,
                -non_en_vals,
                height=bar_h,
                color=MODEL_PALETTE.get(model, SEA_COLORS["black"]),
                alpha=0.5,
                edgecolor=SEA_COLORS["black"],
                linewidth=1.0,
            )
            ax.errorbar(
                -non_en_vals,
                y,
                xerr=np.vstack(
                    [
                        non_en_high - non_en_vals,
                        non_en_vals - non_en_low,
                    ]
                ),
                fmt="none",
                ecolor=SEA_COLORS["black"],
                elinewidth=1.0,
                capsize=2.4,
                alpha=0.8,
                zorder=5,
            )
            ax.barh(
                y,
                en_vals,
                height=bar_h,
                color=MODEL_PALETTE.get(model, SEA_COLORS["black"]),
                alpha=0.85,
                edgecolor=SEA_COLORS["black"],
                linewidth=0.4,
                label=MODEL_LABELS[model],
            )
            ax.errorbar(
                en_vals,
                y,
                xerr=np.vstack(
                    [
                        en_vals - en_low,
                        en_high - en_vals,
                    ]
                ),
                fmt="none",
                ecolor=SEA_COLORS["black"],
                elinewidth=1.0,
                capsize=2.4,
                alpha=0.8,
                zorder=5,
            )
        ax.axvline(0, color=SEA_COLORS["black"], lw=1)
        ax.set_xlim(-xmax, xmax)
        ax.set_yticks(y_base)
        ax.set_yticklabels(domain_order, fontsize=DOMAIN_LABEL_SIZE)
        ax.grid(axis="x", alpha=1.0)
        ax.set_title(
            "$" + metric.replace("rho", "\\rho") + "$",
            pad=14,
            fontsize=TITLE_SIZE,
        )
        ax.set_xticks([-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0])
        ax.xaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _pos: f"{abs(x):.0%}")
        )
        ax.tick_params(axis="x", labelsize=TICK_SIZE)
        ax.text(
            -xmax * 0.98,
            len(domain_order) - 0.6,
            "Non-English",
            ha="left",
            va="bottom",
            fontsize=SIDE_LABEL_SIZE,
            fontweight="bold",
        )
        ax.text(
            xmax * 0.98,
            len(domain_order) - 0.6,
            "English",
            ha="right",
            va="bottom",
            fontsize=SIDE_LABEL_SIZE,
            fontweight="bold",
        )
    fig.text(
        0.5,
        0.015,
        "95% CIs: task bootstrap (EN); language bootstrap (Non-EN).",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=EN_VS_L2_PERF_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    df = pd.read_csv(args.csv)
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
