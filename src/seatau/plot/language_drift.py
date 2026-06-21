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

from seatau.analysis.drift_common import (
    DEFAULT_ANALYSES_DIR,
    FIGURE_SCENARIOS,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    SCENARIO_LABELS,
    SCENARIO_ORDER,
)
from seatau.plot.config import DEFAULT_FIG_DIR, EXPORT_FORMATS
from seatau.plot.plot_utils import apply_style, save_figure

ONE_COL_WIDTH = 3.35
TWO_COL_WIDTH = 7.0

DEFAULT_SUMMARY_DIR = DEFAULT_ANALYSES_DIR / "language_drift_summary"
DEFAULT_DIAGNOSTICS_DIR = DEFAULT_ANALYSES_DIR / "language_drift_diagnostics"

DRIFT_COLORS = {
    "target": "#6BAA75",
    "english": "#D47A2A",
    "other": "#7A87A8",
}
CAUSE_COLORS = {
    "structured_tool_echo": "#8C6D31",
    "post_tool_response": "#7E57A3",
    "follows_user_drift": "#D47A2A",
    "follows_agent_drift": "#D47A2A",
    "continued_user_drift": "#9C7A35",
    "early_turn": "#5A8DB8",
    "transfer_or_system_template": "#666666",
    "other_or_detector_noise": "#BDBDBD",
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
    build_post_tool_language_mix(
        diagnostics["turn"], args.output_dir, tuple(args.formats)
    )
    build_post_tool_exact_languages(
        diagnostics["turn"], args.output_dir, tuple(args.formats)
    )
    build_tool_mix_agent_language_use(
        diagnostics["turn"], args.output_dir, tuple(args.formats)
    )
    build_language_drift_cause_heuristics(
        diagnostics["turn"], args.output_dir, tuple(args.formats)
    )
    build_language_drift_by_turn_position(
        diagnostics["turn"], args.output_dir, tuple(args.formats)
    )
    build_agent_drift_sensitivity_exclusions(
        diagnostics["turn"], args.output_dir, tuple(args.formats)
    )


def load_summary_data(summary_dir: Path) -> dict[str, pd.DataFrame]:
    """Load aggregate language-drift tables."""

    return {
        "overall": pd.read_csv(summary_dir / "language_drift_overall.csv"),
        "task": pd.read_csv(summary_dir / "agent_language_drift_by_task.csv"),
    }


def load_diagnostics_data(diagnostics_dir: Path) -> dict[str, pd.DataFrame]:
    """Load contextual diagnostics tables."""

    return {
        "turn": pd.read_csv(
            diagnostics_dir / "contextual_turn_language.csv",
            low_memory=False,
        ),
        "summary": pd.read_csv(diagnostics_dir / "contextual_language_summary.csv"),
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

    with plt.rc_context({"font.size": 6, "axes.titlesize": 7, "axes.labelsize": 7}):
        fig, axes = plt.subplots(2, 1, figsize=(ONE_COL_WIDTH, 4.15), sharex=True)
        rng = np.random.default_rng(7)
        colors = {"l2_interaction": "#2878A6", "l2_domain": "#CC6B2C"}

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
                medianprops={"color": "#111111", "linewidth": 1.0},
                boxprops={
                    "facecolor": "#F3F3F3",
                    "edgecolor": "#666666",
                    "linewidth": 0.8,
                },
                whiskerprops={"color": "#666666", "linewidth": 0.75},
                capprops={"color": "#666666", "linewidth": 0.75},
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
            ax.grid(axis="y", color="#DDDDDD", linewidth=0.45)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        axes[-1].set_xticks(np.arange(1, len(LANGUAGE_ORDER) + 1))
        axes[-1].set_xticklabels([LANGUAGE_LABELS[lang] for lang in LANGUAGE_ORDER])
        axes[-1].set_xlabel("Target language")
        fig.suptitle("Agent English switching by task", y=0.985, fontsize=8)
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

    with plt.rc_context({"font.size": 7, "axes.titlesize": 8}):
        fig, ax = plt.subplots(figsize=(TWO_COL_WIDTH, 2.95))
        image = ax.imshow(
            data,
            aspect="auto",
            vmin=0,
            vmax=max(0.35, float(np.nanmax(data))),
            cmap="YlOrRd",
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
                    fontsize=6.2,
                    color="white" if value >= 0.28 else "#222222",
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


def build_post_tool_language_mix(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Stacked language buckets for agent turns after tool results vs elsewhere."""

    frame = counted_agent_turns(turn_df)
    frame["context"] = np.where(frame["after_tool_result"], "After tool", "Other turns")
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(["scenario", "context"], sort=False):
        scenario, context = cast(tuple[str, str], key)
        denom = len(group)
        for bucket in ["target", "english", "other"]:
            rows.append(
                {
                    "scenario": scenario,
                    "context": context,
                    "bucket": bucket,
                    "share": safe_rate(
                        group["language_bucket"].eq(bucket).sum(), denom
                    ),
                }
            )
    summary = pd.DataFrame(rows)

    with plt.rc_context({"font.size": 7, "axes.titlesize": 8}):
        fig, axes = plt.subplots(1, 3, figsize=(TWO_COL_WIDTH, 2.15), sharey=True)
        for ax, scenario in zip(axes, SCENARIO_ORDER, strict=True):
            bottom = np.zeros(2)
            contexts = ["After tool", "Other turns"]
            for bucket in ["target", "english", "other"]:
                values = [
                    select_share(summary, scenario, context, bucket)
                    for context in contexts
                ]
                ax.bar(
                    contexts,
                    values,
                    bottom=bottom,
                    color=DRIFT_COLORS[bucket],
                    label=bucket.capitalize(),
                    width=0.62,
                )
                bottom += np.array(values)
            ax.set_title(SCENARIO_LABELS[scenario])
            ax.set_ylim(0, 1)
            ax.grid(axis="y", color="#E1E1E1", linewidth=0.45)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.tick_params(axis="x", rotation=18)
        axes[0].set_ylabel("Share of agent turns")
        axes[-1].legend(frameon=False, bbox_to_anchor=(1.01, 1.0), loc="upper left")
        fig.suptitle("Agent language immediately after tool results", fontsize=9)
        fig.subplots_adjust(left=0.075, right=0.86, bottom=0.24, top=0.76, wspace=0.24)
        save_figure(fig, "agent_post_tool_language_mix", figure_dir, formats)
        plt.close(fig)


def build_post_tool_exact_languages(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Exact detected languages for counted agent turns after tool results."""

    frame = counted_agent_turns(turn_df)
    frame = frame.loc[
        frame["after_tool_result"] & frame["detected_language"].astype(str).ne("")
    ].copy()
    counts = frame["detected_language"].value_counts()
    language_order = counts.head(8).index.tolist()
    frame["language_plot"] = np.where(
        frame["detected_language"].isin(language_order),
        frame["detected_language"],
        "other",
    )
    if "other" in set(frame["language_plot"]):
        language_order.append("other")

    summary = (
        frame.groupby(["scenario", "language_plot"], dropna=False)
        .size()
        .rename("count")
        .reset_index()
    )
    totals = summary.groupby("scenario")["count"].transform("sum")
    summary["share"] = summary["count"] / totals
    colors = {
        "en": "#D47A2A",
        "id": "#4C78A8",
        "th": "#59A14F",
        "tl": "#B07AA1",
        "vi": "#76B7B2",
        "zh": "#E15759",
        "ko": "#9C755F",
        "si": "#F28E2B",
        "other": "#BAB0AC",
    }

    with plt.rc_context({"font.size": 7, "axes.titlesize": 8}):
        fig, ax = plt.subplots(figsize=(TWO_COL_WIDTH, 2.35))
        x = np.arange(len(SCENARIO_ORDER))
        bottom = np.zeros(len(SCENARIO_ORDER))
        for language in language_order:
            values = [
                get_exact_language_share(summary, scenario, language)
                for scenario in SCENARIO_ORDER
            ]
            ax.bar(
                x,
                values,
                bottom=bottom,
                width=0.58,
                color=colors.get(language, "#999999"),
                label=language,
            )
            bottom += np.array(values)
        ax.set_xticks(x)
        ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
        ax.set_ylim(0, 1)
        ax.set_ylabel("Share of post-tool agent turns")
        ax.grid(axis="y", color="#E1E1E1", linewidth=0.45)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            frameon=False, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.18)
        )
        ax.set_title("Exact post-tool detected languages")
        fig.subplots_adjust(left=0.08, right=0.995, bottom=0.32, top=0.84)
        save_figure(fig, "agent_post_tool_detected_languages", figure_dir, formats)
        plt.close(fig)


def build_tool_mix_agent_language_use(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Show agent non-English language use in L2 Tools tool-mix rows."""

    frame = counted_agent_turns(turn_df)
    frame = frame.loc[
        frame["scenario"].eq("l2_tools")
        & frame["language"].astype(str).str.startswith("tool_mix")
    ].copy()
    domains = ["airline", "retail", "telecom"]
    mixes = ["tool_mix_2", "tool_mix_3", "tool_mix_4", "tool_mix_5"]
    data = np.full((len(domains), len(mixes)), np.nan)
    labels = [["" for _ in mixes] for _ in domains]
    for i, domain in enumerate(domains):
        for j, mix in enumerate(mixes):
            subset = frame.loc[frame["domain"].eq(domain) & frame["language"].eq(mix)]
            if subset.empty:
                continue
            non_english = 1 - float(subset["is_english"].mean())
            data[i, j] = non_english * 1000
            counts = subset.loc[
                ~subset["is_english"], "detected_language"
            ].value_counts()
            labels[i][j] = "|".join(counts.head(2).index.astype(str)) or "0"

    with plt.rc_context({"font.size": 6.5, "axes.titlesize": 8}):
        fig, ax = plt.subplots(figsize=(ONE_COL_WIDTH, 1.85))
        vmax = max(1.0, float(np.nanmax(data)))
        image = ax.imshow(data, aspect="auto", cmap="PuBu", vmin=0, vmax=vmax)
        ax.set_xticks(np.arange(len(mixes)))
        ax.set_xticklabels([LANGUAGE_LABELS[mix] for mix in mixes])
        ax.set_yticks(np.arange(len(domains)))
        ax.set_yticklabels([domain.title() for domain in domains])
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                value = data[i, j]
                if np.isnan(value):
                    continue
                ax.text(
                    j,
                    i,
                    f"{value:.1f}\n{labels[i][j]}",
                    ha="center",
                    va="center",
                    fontsize=5.6,
                    color="white" if value > vmax * 0.55 else "#222222",
                )
        cbar = fig.colorbar(image, ax=ax, fraction=0.052, pad=0.02)
        cbar.set_label("Non-English / 1k turns")
        ax.set_title("Tool-mix agent language use")
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.subplots_adjust(left=0.16, right=0.88, bottom=0.18, top=0.82)
        save_figure(fig, "tool_mix_agent_language_use", figure_dir, formats)
        plt.close(fig)


def build_language_drift_cause_heuristics(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Stacked heuristic causes for non-target user and agent turns."""

    drift = turn_df.loc[
        turn_df["is_non_target_language"]
        & turn_df["drift_cause"].ne("target_or_expected_language")
        & turn_df["counted_for_language_correctness"]
    ].copy()
    cause_order = [
        "structured_tool_echo",
        "post_tool_response",
        "follows_user_drift",
        "follows_agent_drift",
        "continued_user_drift",
        "early_turn",
        "transfer_or_system_template",
        "other_or_detector_noise",
    ]

    with plt.rc_context({"font.size": 7, "axes.titlesize": 8}):
        fig, axes = plt.subplots(1, 2, figsize=(TWO_COL_WIDTH, 2.55), sharey=True)
        for ax, role in zip(axes, ["agent", "user"], strict=True):
            subset = drift.loc[drift["role"].eq(role)]
            x = np.arange(len(SCENARIO_ORDER))
            bottom = np.zeros(len(SCENARIO_ORDER))
            for cause in cause_order:
                values = []
                for scenario in SCENARIO_ORDER:
                    scenario_rows = subset.loc[subset["scenario"].eq(scenario)]
                    values.append(
                        safe_rate(
                            scenario_rows["drift_cause"].eq(cause).sum(),
                            len(scenario_rows),
                        )
                        if len(scenario_rows)
                        else 0
                    )
                ax.bar(
                    x,
                    values,
                    bottom=bottom,
                    color=CAUSE_COLORS.get(cause, "#BBBBBB"),
                    width=0.62,
                    label=cause.replace("_", " "),
                )
                bottom += np.array(values, dtype=float)
            ax.set_title(role.capitalize())
            ax.set_xticks(x)
            ax.set_xticklabels(
                [SCENARIO_LABELS[s] for s in SCENARIO_ORDER], rotation=18, ha="right"
            )
            ax.set_ylim(0, 1)
            ax.grid(axis="y", color="#E1E1E1", linewidth=0.45)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        axes[0].set_ylabel("Share of non-target turns")
        axes[-1].legend(
            frameon=False, bbox_to_anchor=(1.01, 1.0), loc="upper left", fontsize=6.2
        )
        fig.suptitle("Heuristic sources of language drift", fontsize=9)
        fig.subplots_adjust(left=0.075, right=0.75, bottom=0.24, top=0.78, wspace=0.18)
        save_figure(fig, "language_drift_cause_heuristics", figure_dir, formats)
        plt.close(fig)


def build_language_drift_by_turn_position(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Plot non-target rate by turn position for user and counted agent turns."""

    frame = turn_df.loc[
        turn_df["turn_idx"].le(24) & turn_df["counted_for_language_correctness"]
    ].copy()
    summary = (
        frame.groupby(["scenario", "role", "turn_idx"], dropna=False)[
            "is_non_target_language"
        ]
        .mean()
        .reset_index(name="non_target_share")
    )
    colors = {"agent": "#2878A6", "user": "#D47A2A"}

    with plt.rc_context({"font.size": 7, "axes.titlesize": 8}):
        fig, axes = plt.subplots(1, 3, figsize=(TWO_COL_WIDTH, 2.2), sharey=True)
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
            ax.grid(axis="y", color="#E1E1E1", linewidth=0.45)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        axes[0].set_ylabel("Non-L2 proportion")
        axes[-1].legend(frameon=False, loc="upper right")
        fig.suptitle("Drift by conversation position", fontsize=9)
        fig.subplots_adjust(left=0.075, right=0.99, bottom=0.24, top=0.78, wspace=0.22)
        save_figure(fig, "language_drift_by_turn_position", figure_dir, formats)
        plt.close(fig)


def build_agent_drift_sensitivity_exclusions(
    turn_df: pd.DataFrame, figure_dir: Path, formats: tuple[str, ...]
) -> None:
    """Compare agent drift under simple opening/template exclusions."""

    agent = turn_df.loc[turn_df["role"].eq("agent")].copy()
    transfer_template = agent["drift_cause"].eq("transfer_or_system_template")
    views = {
        "All agent turns": agent,
        "Drop turn 0": agent.loc[agent["turn_idx"].ne(0)],
        "Counted correctness": agent.loc[agent["counted_for_language_correctness"]],
        "Counted + no templates": agent.loc[
            agent["counted_for_language_correctness"] & ~transfer_template
        ],
        "Only after tool": agent.loc[
            agent["after_tool_result"] & agent["counted_for_language_correctness"]
        ],
    }
    rows: list[dict[str, Any]] = []
    for view_name, view_df in views.items():
        for scenario in SCENARIO_ORDER:
            subset = view_df.loc[view_df["scenario"].eq(scenario)]
            rows.append(
                {
                    "view": view_name,
                    "scenario": scenario,
                    "non_target_share": safe_rate(
                        subset["is_non_target_language"].sum(), len(subset)
                    ),
                }
            )
    summary = pd.DataFrame(rows)

    with plt.rc_context({"font.size": 7, "axes.titlesize": 8}):
        fig, ax = plt.subplots(figsize=(TWO_COL_WIDTH, 2.6))
        x = np.arange(len(SCENARIO_ORDER))
        width = 0.14
        palette = ["#333333", "#5A8DB8", "#6BAA75", "#88B78C", "#7E57A3"]
        for idx, (view_name, color) in enumerate(zip(views, palette, strict=True)):
            values = [
                float(
                    summary.loc[
                        summary["view"].eq(view_name)
                        & summary["scenario"].eq(scenario),
                        "non_target_share",
                    ].iloc[0]
                )
                for scenario in SCENARIO_ORDER
            ]
            ax.bar(
                x + (idx - 2) * width,
                values,
                width=width,
                color=color,
                label=view_name,
            )
        ax.set_xticks(x)
        ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIO_ORDER])
        ax.set_ylabel("Agent non-L2 proportion")
        ax.set_ylim(0, max(0.24, summary["non_target_share"].max() * 1.18))
        ax.grid(axis="y", color="#E1E1E1", linewidth=0.45)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(frameon=False, ncol=2, loc="upper right", fontsize=6.2)
        ax.set_title("Drift sensitivity to opening/template turns")
        fig.subplots_adjust(left=0.08, right=0.99, bottom=0.18, top=0.88)
        save_figure(fig, "agent_drift_sensitivity_exclusions", figure_dir, formats)
        plt.close(fig)


def counted_agent_turns(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Return counted agent turns for correctness-style plots."""

    return turn_df.loc[
        turn_df["role"].eq("agent") & turn_df["counted_for_language_correctness"]
    ].copy()


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
