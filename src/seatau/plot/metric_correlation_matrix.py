"""Plot cross-language correlations for pass@1 and rho^3."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from seatau.plot.config import (
    DEFAULT_CSV_PATH,
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    PLOT_LABEL_SIZE,
    PLOT_TITLE_SIZE,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    apply_style,
    experiment_language_metric_breakdown,
    load_and_prepare,
    save_figure,
)

FIGURE_STEM = "metric_correlation_matrix"


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the upper/lower triangular language correlation matrix."""

    plot_df = df.copy()
    pass_corr = plot_df.loc[plot_df["Metric"].eq("pass@1"), LANGUAGE_ORDER].corr()
    rho_corr = plot_df.loc[plot_df["Metric"].eq("rho^3"), LANGUAGE_ORDER].corr()
    n = len(LANGUAGE_ORDER)
    labels = [LANGUAGE_LABELS.get(lang, lang) for lang in LANGUAGE_ORDER]
    pass_mat = pass_corr.to_numpy().copy()
    rho_mat = rho_corr.to_numpy().copy()
    np.fill_diagonal(pass_mat, np.nan)
    np.fill_diagonal(rho_mat, np.nan)
    upper = np.where(np.triu(np.ones((n, n), dtype=bool), k=1), pass_mat, np.nan)
    lower = np.where(np.tril(np.ones((n, n), dtype=bool), k=-1), rho_mat, np.nan)

    fig, ax = plt.subplots(figsize=(7, 6))
    pass_cmap = LinearSegmentedColormap.from_list(
        "sea_pass_corr", [SEA_COLORS["white"], SEA_COLORS["blue"]]
    )
    rho_cmap = LinearSegmentedColormap.from_list(
        "sea_rho_corr", [SEA_COLORS["white"], SEA_COLORS["red"]]
    )
    im_upper = ax.imshow(np.ma.masked_invalid(upper), cmap=pass_cmap, vmin=0, vmax=1)
    im_lower = ax.imshow(np.ma.masked_invalid(lower), cmap=rho_cmap, vmin=0, vmax=1)
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color=SEA_COLORS["white"], linestyle="-", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(n):
        for j in range(n):
            if i < j:
                value = pass_corr.iat[i, j]
            elif i > j:
                value = rho_corr.iat[i, j]
            else:
                continue
            text_color = SEA_COLORS["white"] if value >= 0.45 else SEA_COLORS["black"]
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=PLOT_TITLE_SIZE,
                color=text_color,
                fontweight="bold",
            )
    cbar1 = fig.colorbar(im_upper, ax=ax, fraction=0.039, pad=-0.2)
    cbar1.set_label("pass@1 corr (upper)", fontsize=PLOT_LABEL_SIZE, fontweight="bold")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    cbar2 = fig.colorbar(
        im_lower, ax=ax, orientation="horizontal", fraction=0.047, pad=0.01
    )
    cbar2.set_label(
        "$\\rho^3$ corr (lower)", fontsize=PLOT_LABEL_SIZE, fontweight="bold"
    )
    cbar2.ax.xaxis.set_label_position("bottom")
    cbar2.ax.xaxis.set_ticks_position("bottom")
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False)
    fig.tight_layout()
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
