"""Plot language drift diagnostics from precomputed analysis CSVs.

This module intentionally does not run fastText or read raw trajectories. Run:

  uv run python -m seatau.analysis.language_drift_summary
  uv run python -m seatau.analysis.language_drift_diagnostics

Then generate figures with:

  uv run python -m seatau.plot.language_drift
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from seatau.constants import LANGUAGE_DRIFT_DIAGNOSTICS_DIR, LANGUAGE_DRIFT_SUMMARY_DIR
from seatau.experiment_matrix import list_supported_domains
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    PLOT_FIGSIZE_ONE_COL_SHORT,
    PLOT_FIGSIZE_ONE_COL_TALL,
    PLOT_FIGSIZE_TWO_COL,
    PLOT_FIGSIZE_TWO_COL_SHORT,
    PLOT_LABEL_SIZE,
    PLOT_LEGEND_SIZE,
    PLOT_TICK_SIZE,
    PLOT_TITLE_SIZE,
    SCENARIO_LABELS,
    SEA_COLORS,
    TOOL_MIX_ORDER,
)
from seatau.plot.config import (
    LANGUAGE_ORDER as CONFIG_LANGUAGE_ORDER,
)
from seatau.plot.config import (
    SCENARIO_ORDER as CONFIG_SCENARIO_ORDER,
)
from seatau.plot.plot_utils import apply_style, normalize_scenario_column, save_figure

DEFAULT_SUMMARY_DIR = LANGUAGE_DRIFT_SUMMARY_DIR
DEFAULT_DIAGNOSTICS_DIR = LANGUAGE_DRIFT_DIAGNOSTICS_DIR
SCENARIO_ORDER = [
    scenario for scenario in CONFIG_SCENARIO_ORDER if scenario != "english"
]
FIGURE_SCENARIOS = ["l2_interaction", "l2_domain"]
LANGUAGE_ORDER = [
    language for language in CONFIG_LANGUAGE_ORDER if language != "english"
]

DRIFT_COLORS = {
    "target": SEA_COLORS["blue"],
    "english": SEA_COLORS["red"],
    "other": SEA_COLORS["yellow"],
}


def main() -> None:
    """Command-line entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-dir", type=Path, default=DEFAULT_SUMMARY_DIR)
    parser.add_argument("--diagnostics-dir", type=Path, default=DEFAULT_DIAGNOSTICS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    args = parser.parse_args()

    apply_style()
    summary = load_summary_data(args.summary_dir)
    diagnostics = load_diagnostics_data(args.diagnostics_dir)

    build_agent_english_share_boxplots(
        summary["task"], args.output_dir, tuple(args.formats)
    )
    build_agent_english_share_by_model_heatmap(
        summary["task"], args.output_dir, tuple(args.formats)
    )
    build_tool_mix_agent_language_use(
        diagnostics["tool_mix"], args.output_dir, tuple(args.formats)
    )
    build_language_drift_by_turn_position(
        diagnostics["turn_position"], args.output_dir, tuple(args.formats)
    )


def load_summary_data(summary_dir: Path) -> dict[str, pd.DataFrame]:
    """Load aggregate language-drift tables."""

    return {
        "task": normalize_scenario_column(
            pd.read_csv(summary_dir / "agent_language_drift_by_task.csv")
        ),
    }


def load_diagnostics_data(diagnostics_dir: Path) -> dict[str, pd.DataFrame]:
    """Load contextual diagnostics tables."""

    return {
        "turn_position": normalize_scenario_column(
            pd.read_csv(
                diagnostics_dir / "contextual_turn_position.csv",
            )
        ),
        "tool_mix": normalize_scenario_column(
            pd.read_csv(diagnostics_dir / "contextual_tool_mix_summary.csv")
        ),
    }


def build_agent_english_share_boxplots(
    task_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """2x1 boxplots of agent English switching by L2 scenario and language."""

    frame = task_df.loc[
        task_df["scenario"].isin(FIGURE_SCENARIOS)
        & task_df["language"].isin(LANGUAGE_ORDER)
    ].copy()
    frame["language"] = pd.Categorical(
        frame["language"], categories=LANGUAGE_ORDER, ordered=True
    )

    fig, axes = plt.subplots(2, 1, figsize=PLOT_FIGSIZE_ONE_COL_TALL, sharex=True)
    rng = np.random.default_rng(7)
    colors = {
        "l2_interaction": SEA_COLORS["blue"],
        "l2_domain": SEA_COLORS["red"],
    }

    for ax, scenario in zip(axes, FIGURE_SCENARIOS, strict=True):
        subset = frame.loc[frame["scenario"].eq(scenario)]
        data = [
            subset.loc[subset["language"].eq(language), "english_turn_share"]
            .dropna()
            .to_numpy()
            for language in LANGUAGE_ORDER
        ]
        positions = np.arange(1, len(LANGUAGE_ORDER) + 1)
        ax.boxplot(
            data,
            positions=positions,
            widths=0.48,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": SEA_COLORS["black"], "linewidth": 1.0},
            boxprops={
                "facecolor": SEA_COLORS["white"],
                "edgecolor": SEA_COLORS["black"],
                "linewidth": 0.8,
            },
            whiskerprops={"color": SEA_COLORS["black"], "linewidth": 0.75},
            capprops={"color": SEA_COLORS["black"], "linewidth": 0.75},
        )
        for idx, values in enumerate(data, start=1):
            if len(values) == 0:
                continue
            jitter = rng.normal(0, 0.04, len(values))
            ax.scatter(
                np.full(len(values), idx) + jitter,
                values,
                s=4,
                color=colors[scenario],
                alpha=0.14,
                linewidths=0,
                zorder=2,
            )
        means = [
            float(np.nanmean(values)) if len(values) else np.nan for values in data
        ]
        ax.plot(
            positions,
            means,
            color=colors[scenario],
            marker="o",
            markersize=2.5,
            linewidth=0.85,
        )
        ax.set_title(SCENARIO_LABELS[scenario], loc="left", pad=2)
        ax.set_ylabel("English share per task")
        ax.set_ylim(-0.02, 1.02)
        ax.grid(axis="y", color=SEA_COLORS["black"], linewidth=0.45, alpha=0.12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    axes[-1].set_xticks(np.arange(1, len(LANGUAGE_ORDER) + 1))
    axes[-1].set_xticklabels([LANGUAGE_LABELS[lang] for lang in LANGUAGE_ORDER])
    axes[-1].set_xlabel("Target language L2")
    fig.suptitle(
        "Agent English switching by task and L2",
        x=0.5,
        y=0.985,
        ha="center",
        fontsize=PLOT_LABEL_SIZE,
    )
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.11, top=0.91, hspace=0.42)
    save_figure(fig, "agent_english_share_boxplots", figure_dir, formats)
    plt.close(fig)


def build_agent_english_share_by_model_heatmap(
    task_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Heatmap showing model-language cells driving English switching."""

    frame = task_df.loc[
        task_df["scenario"].isin(FIGURE_SCENARIOS)
        & task_df["language"].isin(LANGUAGE_ORDER)
    ].copy()
    frame["agent_family"] = frame["agent_family"].replace(
        {"qwen-3-235b-it": "qwen3-235b"}
    )
    summary = (
        frame.groupby(["scenario", "agent_family", "language"], dropna=False)[
            "english_turn_share"
        ]
        .mean()
        .reset_index()
    )
    models = sorted(summary["agent_family"].dropna().unique())
    row_labels: list[tuple[str, str]] = []
    for scenario in FIGURE_SCENARIOS:
        for model_name in models:
            if not summary.loc[
                summary["scenario"].eq(scenario)
                & summary["agent_family"].eq(model_name)
            ].empty:
                row_labels.append((scenario, model_name))

    data = np.full((len(row_labels), len(LANGUAGE_ORDER)), np.nan)
    for i, (scenario, model_name) in enumerate(row_labels):
        for j, language in enumerate(LANGUAGE_ORDER):
            value = summary.loc[
                summary["scenario"].eq(scenario)
                & summary["agent_family"].eq(model_name)
                & summary["language"].eq(language),
                "english_turn_share",
            ]
            if not value.empty:
                data[i, j] = float(value.iloc[0])

    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_TWO_COL)
    image = ax.imshow(
        data,
        aspect="auto",
        vmin=0,
        vmax=max(0.35, float(np.nanmax(data))),
        cmap=LinearSegmentedColormap.from_list(
            "sea_yellow_red",
            [SEA_COLORS["white"], SEA_COLORS["yellow"], SEA_COLORS["red"]],
        ),
    )
    ax.set_xticks(np.arange(len(LANGUAGE_ORDER)))
    ax.set_xticklabels([LANGUAGE_LABELS[lang] for lang in LANGUAGE_ORDER])
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(
        [
            f"{SCENARIO_LABELS[scenario]} | {model_name}"
            for scenario, model_name in row_labels
        ]
    )
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            if np.isnan(value):
                continue
            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=PLOT_LEGEND_SIZE,
                color=SEA_COLORS["white"] if value >= 0.28 else SEA_COLORS["black"],
            )
    cbar = fig.colorbar(image, ax=ax, fraction=0.028, pad=0.012)
    cbar.set_label("Mean task English share")
    ax.tick_params(length=0)
    ax.set_title("Model-language cells driving English drift")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.31, right=0.93, bottom=0.13, top=0.88)
    save_figure(fig, "agent_english_share_by_model_heatmap", figure_dir, formats)
    plt.close(fig)


def build_tool_mix_agent_language_use(
    tool_mix_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Show agent non-English language use in L2 Tools tool-mix rows."""

    frame = tool_mix_df.loc[
        tool_mix_df["scenario"].eq("l2_tools")
        & tool_mix_df["language"].astype(str).str.startswith("tool_mix")
    ].copy()
    domains = list_supported_domains()
    mixes = TOOL_MIX_ORDER
    data = np.full((len(domains), len(mixes)), np.nan)
    labels = [["" for _ in mixes] for _ in domains]
    for i, domain in enumerate(domains):
        for j, mix in enumerate(mixes):
            subset = frame.loc[frame["domain"].eq(domain) & frame["language"].eq(mix)]
            if subset.empty:
                continue
            total_turns = int(subset["turn_count"].sum())
            non_english = int(
                subset.loc[
                    subset["detected_language"].astype(str).ne("en"), "turn_count"
                ].sum()
            )
            data[i, j] = (non_english / total_turns * 100) if total_turns else np.nan
            counts = (
                subset.loc[subset["detected_language"].astype(str).ne("en")]
                .groupby("detected_language", dropna=False)["turn_count"]
                .sum()
                .sort_values(ascending=False)
            )
            labels[i][j] = "|".join(counts.head(2).index.astype(str)) or "0"

    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_ONE_COL_SHORT)
    vmax = max(1.0, float(np.nanmax(data)))
    image = ax.imshow(
        data,
        aspect="auto",
        cmap=LinearSegmentedColormap.from_list(
            "sea_tool_mix_non_english",
            [SEA_COLORS["white"], SEA_COLORS["blue"], SEA_COLORS["red"]],
        ),
        vmin=0,
        vmax=vmax,
    )
    ax.set_xticks(np.arange(len(mixes)))
    ax.set_xticklabels([LANGUAGE_LABELS[mix] for mix in mixes])
    ax.set_yticks(np.arange(len(domains)))
    ax.set_yticklabels([domain.title() for domain in domains])
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            if np.isnan(value):
                continue
            label = labels[i][j]
            if value <= 0 or label in {"", "0"}:
                text = "0"
            else:
                text = f"{value:.2f}\n{label}"
            ax.text(
                j,
                i,
                text,
                ha="center",
                va="center",
                fontsize=PLOT_LEGEND_SIZE,
                color=(
                    SEA_COLORS["white"] if value > vmax * 0.55 else SEA_COLORS["black"]
                ),
            )
    cbar = fig.colorbar(image, ax=ax, fraction=0.052, pad=0.02)
    cbar.set_label("Non-English share of agent turns (%)")
    ax.set_xlabel("Translated tool mix")
    ax.set_ylabel("Task domain")
    fig.suptitle("Tool-mix agent language use", y=0.985, fontsize=8)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.16, right=0.88, bottom=0.16, top=0.82)
    save_figure(fig, "tool_mix_agent_language_use", figure_dir, formats)
    plt.close(fig)


def build_language_drift_by_turn_position(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Plot non-target rate by turn position for user and counted agent turns."""

    summary = turn_df.loc[turn_df["turn_idx"].le(24)].copy()
    colors = {"agent": SEA_COLORS["blue"], "user": SEA_COLORS["red"]}

    fig, axes = plt.subplots(1, 3, figsize=PLOT_FIGSIZE_TWO_COL_SHORT, sharey=True)
    for ax, scenario in zip(axes, SCENARIO_ORDER, strict=True):
        for role in ["agent", "user"]:
            subset = summary.loc[
                summary["scenario"].eq(scenario) & summary["role"].eq(role)
            ]
            ax.plot(
                subset["turn_idx"],
                subset["non_target_share"],
                marker="o",
                markersize=2,
                linewidth=1.0,
                color=colors[role],
                label=role.capitalize(),
            )
        ax.set_title(SCENARIO_LABELS[scenario])
        ax.set_xlabel("Turn index")
        ax.set_ylim(0, 0.22)
        ax.grid(axis="y", color=SEA_COLORS["black"], linewidth=0.45, alpha=0.12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("Non-L2 proportion")
    axes[-1].legend(frameon=False, loc="upper right")
    fig.suptitle(
        "Language drift by agent turn position in a conversation",
        fontsize=PLOT_TITLE_SIZE,
    )
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.24, top=0.78, wspace=0.22)
    save_figure(fig, "language_drift_by_turn_position", figure_dir, formats)
    plt.close(fig)


def select_share(
    summary: pd.DataFrame, scenario: str, context: str, bucket: str
) -> float:
    """Read a bucket share from a summary table."""

    value = summary.loc[
        summary["scenario"].eq(scenario)
        & summary["context"].eq(context)
        & summary["bucket"].eq(bucket),
        "share",
    ]
    return float(value.iloc[0]) if not value.empty else 0.0


def get_exact_language_share(
    summary: pd.DataFrame, scenario: str, language: str
) -> float:
    """Read an exact-language share from a summary table."""

    value = summary.loc[
        summary["scenario"].eq(scenario) & summary["language_plot"].eq(language),
        "share",
    ]
    return float(value.iloc[0]) if not value.empty else 0.0


def safe_rate(numerator: Any, denominator: Any) -> float:
    """Return a rounded rate, using zero for empty denominators."""

    denom = int(denominator)
    return round(float(numerator) / denom, 6) if denom else 0.0


if __name__ == "__main__":
    main()
