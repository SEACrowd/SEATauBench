"""Plot English scores against average non-English scores by domain."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from seatau.plot.config import (
    DEFAULT_CSV_PATH,
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_ORDER,
    MODEL_LABELS,
    PLOT_LABEL_SIZE,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    MODEL_PALETTE,
    apply_style,
    experiment_language_metric_breakdown,
    load_and_prepare,
    save_figure,
)

FIGURE_STEM = "en_vs_l2_perf"


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the diverging English versus non-English bar chart."""

    domains = df["Domain"].unique()
    plot_df = df.copy()
    metrics = plot_df["Metric"].unique()
    preferred_domain_order = ["Retail", "Airline", "Telecom"]
    domain_order = [d for d in preferred_domain_order if d in domains]
    domain_order += [d for d in domains if d not in domain_order]
    models = plot_df["Model"].unique()
    non_en_langs = [lang for lang in LANGUAGE_ORDER if lang != "english"]
    non_en_series = plot_df[non_en_langs].mean(axis=1, skipna=True)
    max_val = np.nanmax(np.r_[plot_df["english"].to_numpy(), non_en_series.to_numpy()])
    xmax = min(1.0, max_val * 1.15)

    fig, axes = plt.subplots(
        len(metrics), 1, figsize=(6, 2.5 * len(metrics)), squeeze=False
    )
    y_base = np.arange(len(domain_order))
    offsets = (
        np.linspace(-0.18, 0.18, len(models)) if len(models) > 1 else np.array([0.0])
    )
    for i, metric in enumerate(metrics):
        ax = axes[i, 0]
        for j, model in enumerate(models):
            sub = (
                plot_df.loc[plot_df["Metric"].eq(metric) & plot_df["Model"].eq(model)]
                .set_index("Domain")
                .reindex(domain_order)
            )
            en_vals = sub["english"].to_numpy(dtype=float)
            non_en_vals = (
                sub[non_en_langs].mean(axis=1, skipna=True).to_numpy(dtype=float)
            )
            y = y_base + offsets[j]
            bar_h = 0.32 / max(len(models), 1)
            ax.barh(
                y,
                -non_en_vals,
                height=bar_h,
                color=MODEL_PALETTE.get(model, SEA_COLORS["black"]),
                alpha=0.5,
                edgecolor=SEA_COLORS["black"],
                linewidth=1.0,
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
        ax.axvline(0, color=SEA_COLORS["black"], lw=1)
        ax.set_xlim(-xmax, xmax)
        ax.set_yticks(y_base)
        ax.set_yticklabels(domain_order)
        ax.grid(axis="x", alpha=1.0)
        ax.set_title("$" + metric.replace("rho", "\\rho") + "$", pad=12)
        ax.set_xticks([-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0])
        ax.xaxis.set_major_formatter(
            mtick.FuncFormatter(lambda x, _pos: f"{abs(x):.0%}")
        )
        ax.text(
            -xmax * 0.98,
            len(domain_order) - 0.6,
            "Non-English",
            ha="left",
            va="bottom",
            fontsize=PLOT_LABEL_SIZE,
            fontweight="bold",
        )
        ax.text(
            xmax * 0.98,
            len(domain_order) - 0.6,
            "English",
            ha="right",
            va="bottom",
            fontsize=PLOT_LABEL_SIZE,
            fontweight="bold",
        )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
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
