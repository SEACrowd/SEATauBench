"""Scatter agent language correctness against pass^3."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    PLOT_COLUMN_WIDTH,
    SEA_COLORS,
)
from seatau.plot.language_degradation_shared import (
    DEFAULT_ANALYSIS_DIR,
    DEFAULT_LANGUAGE_DIAGNOSTICS_DIR,
    _read_first_existing_analysis_csv,
    _refresh_crosslingual_language_correctness,
)
from seatau.plot.plot_utils import apply_style, despine, save_figure

FIGURE_STEM = "language_vs_perf_corr"


def build_language_vs_perf(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Build and save the correctness-versus-pass^3 scatter plot."""

    df = _read_first_existing_analysis_csv(
        analysis_dir, ("experiment_language_summary.csv", "language_use_summary.csv")
    )
    df["pass_hat_3"] = pd.to_numeric(df["pass_hat_3"], errors="coerce")
    df["agent_language_correctness"] = pd.to_numeric(
        df["agent_language_correctness"], errors="coerce"
    )
    df = _refresh_crosslingual_language_correctness(
        df, DEFAULT_LANGUAGE_DIAGNOSTICS_DIR
    )
    df = df.dropna(subset=["pass_hat_3", "agent_language_correctness"])
    scenario_order = ["english", "l2_tools", "l2_interaction", "l2_domain"]
    scenario_labels = {
        "english": "En Baseline",
        "l2_tools": "L2 Tools",
        "l2_interaction": "L2 Interaction",
        "l2_domain": "L2 Domain",
    }
    scenario_colors = {
        "english": SEA_COLORS["black"],
        "l2_tools": SEA_COLORS["blue"],
        "l2_interaction": SEA_COLORS["yellow"],
        "l2_domain": SEA_COLORS["red"],
    }

    # One-column figure with extra height for the title, x-label, and legend.
    fig, ax = plt.subplots(figsize=(PLOT_COLUMN_WIDTH, 2.9))
    grouped = {
        scenario: frame
        for scenario, frame in df.groupby("scenario", sort=False, dropna=False)
    }
    if len(df) >= 3:
        x = df["agent_language_correctness"].to_numpy(dtype=float)
        y = df["pass_hat_3"].to_numpy(dtype=float)
        fit = np.polyfit(x, y, deg=1)
        x_line = np.linspace(max(0.45, np.nanmin(x)), 1.0, 80)
        ax.plot(
            x_line,
            fit[0] * x_line + fit[1],
            color=SEA_COLORS["black"],
            linewidth=1.0,
            alpha=0.7,
            zorder=2,
        )
        corr = np.corrcoef(x, y)[0, 1]
        ax.text(
            0.03,
            0.05,
            f"R²={corr * corr:.3f}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
        )
    for scenario in scenario_order:
        sub = grouped.get(scenario)
        if sub is None or sub.empty:
            continue
        ax.scatter(
            sub["agent_language_correctness"],
            sub["pass_hat_3"],
            s=42,
            alpha=0.9,
            color=scenario_colors[scenario],
            edgecolor=SEA_COLORS["black"],
            linewidth=0.25,
            label=scenario_labels[scenario],
            zorder=3,
        )
    ax.set_xlabel("Mean agent language correctness")
    ax.set_ylabel(r"pass$^3$")
    ax.set_title(
        "Language correctness vs. pass$^3$",
        pad=6,
    )
    ax.set_xlim(0.45, 1.01)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.25)
    despine(ax)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles[: len(scenario_order)],
        labels[: len(scenario_order)],
        loc="lower center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 0.015),
        handletextpad=0.45,
        columnspacing=0.9,
        borderaxespad=0,
    )
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.3, top=0.84)
    save_figure(fig, FIGURE_STEM, fig_dir, formats)
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    build_language_vs_perf(args.analysis_dir, args.output_dir, tuple(args.formats))
    plt.close("all")


if __name__ == "__main__":
    main()
