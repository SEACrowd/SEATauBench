"""Heatmap of user and agent language correctness by scenario.

Usage:
    python -m seatau.plot.language_correctness_heatmap
    python -m seatau.plot.language_correctness_heatmap --analysis-dir path/to/analysis --output-dir path/to/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    REPO_ROOT,
    SCENARIO_LABELS,
)
from seatau.plot.plot_utils import apply_style, despine, save_figure

DEFAULT_ANALYSIS_DIR = REPO_ROOT / "experiments" / "all_results_analysis"
LANGUAGE_FIGURE_LANGS = ["thai", "vietnamese", "filipino", "indonesian", "chinese"]
ROLE_LABELS = {"user": "User", "agent": "Agent"}
LANGUAGE_CORRECTNESS_CMAP = LinearSegmentedColormap.from_list(
    "language_correctness_soft",
    ["#4A4E74", "#3F8F9D", "#88C5A6", "#E9DF8F"],
)


def _read_analysis_csv(analysis_dir: Path, name: str) -> pd.DataFrame:
    path = analysis_dir / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `uv run analyze-all-results --output-dir {analysis_dir}` first."
        )
    return pd.read_csv(path)


def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def build_language_correctness_heatmap(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Build and save the user/agent language correctness heatmap.

    Args:
        analysis_dir: Directory containing `experiment_language_summary.csv`.
        fig_dir: Directory to write figure files into.
        formats: Output figure formats.

    Returns:
        The generated Matplotlib figure.
    """

    df = _read_analysis_csv(analysis_dir, "experiment_language_summary.csv")
    rows = []
    for role in ("user", "agent"):
        col = f"{role}_language_correctness"
        part = df.loc[df[col].notna()].copy()
        part["role"] = role
        part["language_correctness"] = pd.to_numeric(part[col], errors="coerce")
        rows.append(part)
    long = pd.concat(rows, ignore_index=True)
    long = long.loc[long["language_scenario"].isin(LANGUAGE_FIGURE_LANGS + ["english"])]
    summary = (
        long.groupby(["role", "scenario", "language_scenario"], dropna=False)[
            "language_correctness"
        ]
        .mean()
        .reset_index()
    )
    scenario_order = [
        "1-english-only",
        "2-multilingual-tools",
        "3-crosslingual",
        "4-translated",
    ]
    lang_order = ["english", *LANGUAGE_FIGURE_LANGS]

    with plt.rc_context(
        {
            "font.family": ["Helvetica Neue", "Avenir Next", "DejaVu Sans"],
            "font.weight": "regular",
            "axes.titleweight": "regular",
            "figure.titleweight": "regular",
            "axes.titlesize": 9,
            "figure.titlesize": 10,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
        }
    ):
        fig = plt.figure(figsize=(7.45, 2.35))
        grid = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.028], wspace=0.07)
        axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
        cax = fig.add_subplot(grid[0, 2])
        im = None
        for ax, role in zip(axes, ("user", "agent"), strict=True):
            pivot = (
                summary.loc[summary["role"].eq(role)]
                .pivot(
                    index="scenario",
                    columns="language_scenario",
                    values="language_correctness",
                )
                .reindex(index=scenario_order, columns=lang_order)
            )
            data = pivot.to_numpy(dtype=float)
            im = ax.imshow(
                data,
                vmin=0.45,
                vmax=1.0,
                cmap=LANGUAGE_CORRECTNESS_CMAP,
                aspect="auto",
            )
            ax.set_title(f"{ROLE_LABELS[role]} language correctness", pad=4)
            ax.set_xticks(np.arange(len(lang_order)))
            ax.set_xticklabels(
                [_language_label(lang) for lang in lang_order], rotation=0
            )
            ax.set_yticks(np.arange(len(scenario_order)))
            if role == "user":
                ax.set_yticklabels([SCENARIO_LABELS[int(s[0])] for s in scenario_order])
            else:
                ax.set_yticklabels([])
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    value = data[i, j]
                    if np.isnan(value):
                        continue
                    color = "white" if value < 0.74 else "#111111"
                    ax.text(
                        j,
                        i,
                        f"{value:.2f}",
                        ha="center",
                        va="center",
                        color=color,
                        fontsize=7,
                    )
            ax.tick_params(length=0, pad=2)
            despine(ax)
        if im is None:
            raise ValueError("No heatmap data available for language correctness.")
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label("Mean turn-level correctness", labelpad=6)
        cbar.ax.tick_params(length=3, pad=2)
        fig.suptitle(
            "Language correctness is high in translated runs, but agent drift appears in crosslingual runs",
            y=0.995,
        )
        fig.subplots_adjust(
            left=0.085,
            right=0.94,
            bottom=0.12,
            top=0.82,
            wspace=0.04,
        )
        save_figure(fig, "language_correctness_heatmap", fig_dir, formats)
        return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    args = parser.parse_args()

    apply_style()
    build_language_correctness_heatmap(
        args.analysis_dir, args.output_dir, tuple(args.formats)
    )
    plt.close("all")


if __name__ == "__main__":
    main()
