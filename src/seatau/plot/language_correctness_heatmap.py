"""Heatmap of agent language correctness by scenario and target language.

This figure uses the turn-level language drift diagnostics so crosslingual runs
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

from seatau.analysis.drift_common import (
    DEFAULT_ANALYSES_DIR,
    SCENARIO_LABELS,
    SCENARIO_ORDER,
)
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
)
from seatau.plot.plot_utils import apply_style, despine, save_figure

DEFAULT_DIAGNOSTICS_DIR = DEFAULT_ANALYSES_DIR / "language_drift_diagnostics"
LANGUAGE_CORRECTNESS_CMAP = LinearSegmentedColormap.from_list(
    "agent_language_correctness_contrast",
    ["#16324F", "#2A9D8F", "#F4D35E"],
)


def _read_analysis_csv(analysis_dir: Path, name: str) -> pd.DataFrame:
    path = analysis_dir / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `uv run python -m seatau.analysis.language_drift_diagnostics` first."
        )
    return pd.read_csv(path, low_memory=False)


def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def build_language_correctness_heatmap(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Build and save the agent language correctness heatmap."""

    turn_df = _read_analysis_csv(analysis_dir, "contextual_turn_language.csv")
    frame = turn_df.loc[
        turn_df["role"].eq("agent")
        & turn_df["counted_for_language_correctness"].astype(bool)
        & ~turn_df["is_system_error"].astype(bool)
    ].copy()
    if frame.empty:
        raise ValueError("No agent turns available for language correctness heatmap.")

    frame["is_target_language"] = pd.to_numeric(
        frame["is_target_language"], errors="coerce"
    ).fillna(0.0)

    experiment_scores = (
        frame.groupby(
            [
                "experiments_all_line",
                "scenario",
                "domain",
                "language",
                "agent_llm",
                "normalized_agent_llm",
                "simulation_source",
            ],
            dropna=False,
        )["is_target_language"]
        .mean()
        .rename("agent_language_correctness")
        .reset_index()
    )
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
            "font.family": ["Helvetica Neue", "Avenir Next", "DejaVu Sans"],
            "font.weight": "regular",
            "axes.titleweight": "regular",
            "figure.titleweight": "regular",
            "axes.titlesize": 8.5,
            "figure.titlesize": 9,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
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
        ).reindex(index=SCENARIO_ORDER, columns=lang_order)
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
        ax.set_yticks(np.arange(len(SCENARIO_ORDER)))
        ax.set_yticklabels([SCENARIO_LABELS[scenario] for scenario in SCENARIO_ORDER])
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                value = data[i, j]
                if np.isnan(value):
                    continue
                color = "white" if value < 0.84 else "#111111"
                ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=5.8,
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
