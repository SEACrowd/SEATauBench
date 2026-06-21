"""Plot cross-language correlations for pass@1 and rho^3."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from seatau.plot.plot_utils import apply_style
from seatau.plot.seatau_recap_common import (
    LANGUAGE_LABELS,
    LANGUAGES,
    RECAP_BREAKDOWN_PATH,
    add_format_args,
    read_recap_breakdown,
    recap_breakdown_metrics,
    save_figure,
)

FIGURE_STEM = "language_metric_correlation_matrix"


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the upper/lower triangular language correlation matrix."""

    plot_df = recap_breakdown_metrics(df)
    pass_corr = plot_df.loc[plot_df["Metric"].eq("pass@1"), LANGUAGES].corr()
    rho_corr = plot_df.loc[plot_df["Metric"].eq("rho^3"), LANGUAGES].corr()
    n = len(LANGUAGES)
    labels = [LANGUAGE_LABELS.get(lang, lang) for lang in LANGUAGES]
    pass_mat = pass_corr.to_numpy().copy()
    rho_mat = rho_corr.to_numpy().copy()
    np.fill_diagonal(pass_mat, np.nan)
    np.fill_diagonal(rho_mat, np.nan)
    upper = np.where(np.triu(np.ones((n, n), dtype=bool), k=1), pass_mat, np.nan)
    lower = np.where(np.tril(np.ones((n, n), dtype=bool), k=-1), rho_mat, np.nan)

    fig, ax = plt.subplots(figsize=(7, 6))
    purple_cmap = LinearSegmentedColormap.from_list(
        "white_purple", ["#ffffff", "#6a0dad"]
    )
    im_upper = ax.imshow(np.ma.masked_invalid(upper), cmap=purple_cmap, vmin=0, vmax=1)
    im_lower = ax.imshow(
        np.ma.masked_invalid(lower), cmap=plt.cm.Greens.copy(), vmin=0, vmax=1
    )
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(n):
        for j in range(n):
            if i < j:
                value = pass_corr.iat[i, j]
            elif i > j:
                value = rho_corr.iat[i, j]
            else:
                continue
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=12,
                color="white",
                fontweight="bold",
            )
    cbar1 = fig.colorbar(im_upper, ax=ax, fraction=0.039, pad=-0.2)
    cbar1.set_label("pass@1 corr (upper)", fontsize=12, fontweight="bold")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    cbar2 = fig.colorbar(
        im_lower, ax=ax, orientation="horizontal", fraction=0.047, pad=0.01
    )
    cbar2.set_label("$\\rho^3$ corr (lower)", fontsize=12, fontweight="bold")
    cbar2.ax.xaxis.set_label_position("bottom")
    cbar2.ax.xaxis.set_ticks_position("bottom")
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False)
    fig.tight_layout()
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
