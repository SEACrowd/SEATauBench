"""Performance degradation by language with per-model dots.

One panel per non-English target language (TH, VI, TL, ID, ZH). Each panel is a
line chart showing how the aggregate score (pass@1, rho^3) falls as the scenario
moves from En Baseline through L2 Interaction, L2 Tools, and L2 Domain.

L2 Interaction and L2 Domain use all four models; L2 Tools and En Baseline use
only the two primary models (GPT 5 Mini, Qwen3 235B).

Usage:
    python -m seatau.plot.language_degradation
    python -m seatau.plot.language_degradation --csv path/to/data.csv --output-dir path/to/figures
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from seatau.plot.config import (
    DEFAULT_CSV_PATH,
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    PLOT_PANEL_SIZE,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    MODEL_ORDER,
    NON_BASELINE_SCENARIO_ORDER,
    SCENARIO_LABELS,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    METRIC_PALETTE,
    apply_style,
    despine,
    load_and_prepare,
    save_figure,
)

# Models shown across all conditions. Edit this list to change the subset.
# Must have data in ALL scenarios to avoid biased line means at conditions with partial coverage.
INCLUDED_MODELS: list[str] = ["gpt-5-mini", "qwen-3-235b-it", "kimi-k2.5"]
DISPLAY_METRICS = ("pass@1", "rho^3")


def _allowed_models(_condition: str) -> list[str]:
    return INCLUDED_MODELS


def _build_frame(
    plot_df: pd.DataFrame,
    target_languages: list[str],
    condition_order: list[str],
) -> pd.DataFrame:
    """Combine EN Baseline rows (replicated per language) with scenario rows."""
    baseline = plot_df.loc[
        plot_df["scenario_raw"].eq("english")
        & plot_df["language_key"].eq("english")
        & plot_df["language_group"].eq("language")
    ].copy()
    baseline["condition"] = SCENARIO_LABELS["english"]

    expanded_baseline: list[pd.DataFrame] = []
    for lang in target_languages:
        copy = baseline.copy()
        copy["panel_language"] = lang
        copy["panel_label"] = LANGUAGE_LABELS.get(lang, lang)
        expanded_baseline.append(copy)

    available_scenarios = set(plot_df["scenario_raw"].dropna())
    scenarios = [s for s in NON_BASELINE_SCENARIO_ORDER if s in available_scenarios]

    lang_rows = plot_df.loc[
        plot_df["scenario_raw"].isin(scenarios)
        & plot_df["language_key"].isin(target_languages)
        & plot_df["language_group"].eq("language")
    ].copy()
    lang_rows["condition"] = lang_rows["scenario_raw"].map(SCENARIO_LABELS)
    lang_rows["panel_language"] = lang_rows["language_key"]
    lang_rows["panel_label"] = lang_rows["language_label"]

    full_frame = pd.concat(expanded_baseline + [lang_rows], ignore_index=True)

    parts: list[pd.DataFrame] = []
    for condition in condition_order:
        allowed = set(_allowed_models(condition))
        parts.append(
            full_frame.loc[
                full_frame["condition"].eq(condition)
                & full_frame["model_key"].isin(allowed)
            ]
        )
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def build_language_degradation(
    clean_df: pd.DataFrame,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    available_langs = set(
        clean_df.loc[clean_df["language_group"].eq("language"), "language_key"].dropna()
    )
    target_languages = [
        lang for lang in LANGUAGE_ORDER if lang in available_langs and lang != "english"
    ]

    available_scenarios = set(clean_df["scenario_raw"].dropna())
    scenarios = [s for s in NON_BASELINE_SCENARIO_ORDER if s in available_scenarios]
    condition_order = [SCENARIO_LABELS["english"]] + [
        SCENARIO_LABELS[s] for s in scenarios
    ]

    plot_df = clean_df.loc[clean_df["model_key"].isin(INCLUDED_MODELS)].copy()
    frame = _build_frame(plot_df, target_languages, condition_order)

    metric_labels = {"pass@1": "pass@1", "rho^3": r"$\rho^3$"}

    n_panels = max(1, len(target_languages))
    n_cols = min(3, n_panels)
    n_rows = math.ceil(n_panels / n_cols)
    panel_width, panel_height = PLOT_PANEL_SIZE
    fig = plt.figure(figsize=(panel_width * n_cols, panel_height * n_rows))
    grid = fig.add_gridspec(n_rows, n_cols * 2)

    axes_flat: list[plt.Axes] = []
    for panel_idx in range(len(target_languages)):
        row_idx = panel_idx // n_cols
        col_idx = panel_idx % n_cols
        panels_in_row = min(n_cols, len(target_languages) - row_idx * n_cols)
        row_offset = n_cols - panels_in_row
        start_col = col_idx * 2 + row_offset
        share_axis = axes_flat[0] if axes_flat else None
        axes_flat.append(
            fig.add_subplot(grid[row_idx, start_col : start_col + 2], sharey=share_axis)
        )

    x_positions = np.arange(len(condition_order))
    score_ticks = np.linspace(0, 1, 6)
    metric_offsets = {
        m: offset
        for m, offset in zip(
            DISPLAY_METRICS, np.linspace(-0.045, 0.045, len(DISPLAY_METRICS))
        )
    }
    model_offsets = {
        m: offset
        for m, offset in zip(MODEL_ORDER, np.linspace(-0.03, 0.03, len(MODEL_ORDER)))
    }

    for ax, language in zip(axes_flat, target_languages):
        subset = frame.loc[frame["panel_language"].eq(language)]

        for metric in DISPLAY_METRICS:
            stats = (
                subset.groupby("condition")[metric]
                .agg(["mean", "std", "count"])
                .reindex(condition_order)
            )
            y_values = stats["mean"].to_numpy(dtype=float).copy()
            sem = stats["std"].fillna(0) / np.sqrt(stats["count"].clip(lower=1))
            y_errors = sem.to_numpy(dtype=float).copy()
            y_errors[np.isnan(y_values)] = np.nan

            dot_summary = (
                subset.groupby(["condition", "model_key"])[metric].mean().reset_index()
            )
            for cond_idx, condition in enumerate(condition_order):
                cond_dots = dot_summary.loc[
                    dot_summary["condition"].eq(condition)
                ].dropna(subset=[metric])
                if cond_dots.empty:
                    continue
                dot_x = np.array(
                    [
                        x_positions[cond_idx]
                        + metric_offsets[metric]
                        + model_offsets.get(m, 0)
                        for m in cond_dots["model_key"]
                    ],
                    dtype=float,
                )
                ax.scatter(
                    dot_x,
                    cond_dots[metric].to_numpy(dtype=float),
                    s=22,
                    marker="o",
                    color=METRIC_PALETTE[metric],
                    edgecolor=SEA_COLORS["white"],
                    linewidth=0.35,
                    alpha=0.75,
                    zorder=4,
                )

            ax.errorbar(
                x_positions,
                y_values,
                yerr=y_errors,
                marker="o",
                markersize=4,
                linewidth=1.6,
                capsize=2.5,
                color=METRIC_PALETTE[metric],
                label=metric_labels[metric],
                zorder=3,
            )

        lang_label = LANGUAGE_LABELS.get(language, language)
        lang_display = LANGUAGE_DISPLAY_NAMES.get(language, language)
        ax.set_title(f"{lang_label} ({lang_display})")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(condition_order, rotation=20, ha="right")
        ax.set_ylim(0, 1.02)
        ax.set_yticks(score_ticks)
        ax.set_yticklabels([f"{t:g}" for t in score_ticks])
        ax.tick_params(axis="y", labelleft=True)
        ax.set_ylabel("Score")
        ax.grid(axis="y", alpha=0.35)
        despine(ax)

    if axes_flat:
        metric_label_map = {"pass@1": "pass@1", "rho^3": r"$\rho^3$"}
        handles = []
        for m in DISPLAY_METRICS:
            color = METRIC_PALETTE[m]
            label = metric_label_map[m]
            handles.append(
                Line2D(
                    [0],
                    [0],
                    color=color,
                    marker="o",
                    markersize=4,
                    linewidth=1.6,
                    label=f"{label} scenario avg",
                )
            )
            handles.append(
                Line2D(
                    [0],
                    [0],
                    color=color,
                    marker="o",
                    markersize=5,
                    linewidth=0,
                    alpha=0.75,
                    label=f"{label} model avg",
                )
            )
        fig.legend(
            handles=handles,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.035),
            ncol=len(handles),
            frameon=False,
            handlelength=1.4,
            handletextpad=0.45,
            columnspacing=1.0,
            borderaxespad=0,
        )
    fig.tight_layout(rect=(0, 0.085, 1, 1), h_pad=0.8, w_pad=0.7)
    save_figure(fig, "language_degradation", fig_dir, formats)
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
    _, _, clean_df, duplicate_summary, audit = load_and_prepare(args.csv)

    print("Audit:")
    for k, v in audit.items():
        print(f"  {k}: {v}")
    if not duplicate_summary.empty:
        print(f"\nDuplicate groups resolved ({len(duplicate_summary)}):")
        print(duplicate_summary.to_string(index=False))

    build_language_degradation(clean_df, args.output_dir, tuple(args.formats))
    plt.close("all")


if __name__ == "__main__":
    main()
