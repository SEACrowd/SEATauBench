"""Heatmap of agent language correctness by scenario and target language.

This figure uses the per-run language drift diagnostics so crosslingual runs
exclude the first agent text turn when counting correctness.

Usage:
    python -m seatau.plot.language_correctness_heatmap
    python -m seatau.plot.language_correctness_heatmap --analysis-dir path/to/diagnostics --output-dir path/to/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from seatau.constants import LANGUAGE_DRIFT_DIAGNOSTICS_DIR
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    PLOT_FONT_FAMILY,
    PLOT_LABEL_SIZE,
    PLOT_TICK_SIZE,
    PLOT_TITLE_SIZE,
    SCENARIO_LABELS,
    SCENARIO_ORDER,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    apply_style,
    despine,
    normalize_scenario_column,
    save_figure,
)

DEFAULT_DIAGNOSTICS_DIR = LANGUAGE_DRIFT_DIAGNOSTICS_DIR
HEATMAP_SCENARIO_ORDER = [
    scenario for scenario in SCENARIO_ORDER if scenario != "english"
]
LANGUAGE_CORRECTNESS_CMAP = LinearSegmentedColormap.from_list(
    "agent_language_correctness_contrast",
    [SEA_COLORS["yellow"], SEA_COLORS["red"]],
)


def _read_analysis_csv(analysis_dir: Path, name: str) -> pd.DataFrame:
    path = analysis_dir / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `uv run python -m seatau.analysis.language_drift_diagnostics` first."
        )
    return normalize_scenario_column(pd.read_csv(path, low_memory=False))


def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def build_language_correctness_heatmap(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Build and save the agent language correctness heatmap."""

    run_df = _read_analysis_csv(analysis_dir, "contextual_run_language.csv")
    frame = run_df.loc[
        run_df["role"].eq("agent") & run_df["turn_count"].astype(float).gt(0)
    ].copy()
    if frame.empty:
        raise ValueError("No agent turns available for language correctness heatmap.")

    experiment_scores = frame[
        [
            "experiments_all_line",
            "scenario",
            "domain",
            "language",
            "agent_llm",
            "normalized_agent_llm",
            "simulation_source",
            "language_correctness",
        ]
    ].rename(columns={"language_correctness": "agent_language_correctness"})
    summary = (
        experiment_scores.groupby(["scenario", "language"], dropna=False)[
            "agent_language_correctness"
        ]
        .mean()
        .reset_index()
    )

    lang_order = [language for language in LANGUAGE_ORDER if language != "english"]
    summary = summary.loc[summary["language"].isin(lang_order)]

    with plt.rc_context(
        {
            "font.family": PLOT_FONT_FAMILY,
            "font.weight": "regular",
            "axes.titleweight": "regular",
            "figure.titleweight": "regular",
            "axes.titlesize": PLOT_TITLE_SIZE,
            "figure.titlesize": PLOT_TITLE_SIZE,
            "axes.labelsize": PLOT_LABEL_SIZE,
            "xtick.labelsize": PLOT_TICK_SIZE,
            "ytick.labelsize": PLOT_TICK_SIZE,
        }
    ):
        fig = plt.figure(figsize=(3.35, 2.45))
        grid = fig.add_gridspec(1, 2, width_ratios=[1, 0.03], wspace=0.06)
        ax = fig.add_subplot(grid[0, 0])
        cax = fig.add_subplot(grid[0, 1])

        pivot = summary.pivot(
            index="scenario",
            columns="language",
            values="agent_language_correctness",
        ).reindex(index=HEATMAP_SCENARIO_ORDER, columns=lang_order)
        data = pivot.to_numpy(dtype=float)
        image = ax.imshow(
            data,
            aspect="auto",
            vmin=0.7,
            vmax=1.0,
            cmap=LANGUAGE_CORRECTNESS_CMAP,
        )
        ax.set_xticks(np.arange(len(lang_order)))
        ax.set_xticklabels([_language_label(lang) for lang in lang_order], rotation=0)
        ax.set_yticks(np.arange(len(HEATMAP_SCENARIO_ORDER)))
        ax.set_yticklabels(
            [SCENARIO_LABELS[scenario] for scenario in HEATMAP_SCENARIO_ORDER]
        )
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                value = data[i, j]
                if np.isnan(value):
                    continue
                color = SEA_COLORS["white"] if value < 0.9 else SEA_COLORS["black"]
                ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=PLOT_TICK_SIZE,
                )
        ax.tick_params(length=0, pad=2)
        despine(ax)
        cbar = fig.colorbar(image, cax=cax)
        cbar.set_label("Mean turn correctness", labelpad=4)
        cbar.ax.tick_params(length=3, pad=2)
        ax.set_title("Agent language correctness", pad=4)
        fig.subplots_adjust(left=0.18, right=0.95, bottom=0.12, top=0.86)
        save_figure(fig, "language_correctness_heatmap", fig_dir, formats)
        return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_DIAGNOSTICS_DIR)
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
