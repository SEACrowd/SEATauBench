"""Performance degradation by language with per-model dots.

One panel per non-English target language (TH, VI, TL, ID, ZH).  Each panel is a line
chart showing how the aggregate score (pass@1, rho^3) falls as the scenario moves from
EN Baseline through L2 Interaction, L2 Tools, and L2 Domain.  Individual model averages
are overlaid as scatter dots in the same color as the metric line.

Scenarios 3 and 4 use all four models; scenario 2 (L2 Tools) and EN Baseline use only
the two primary models (GPT-5 Mini, Qwen3-235B-A22B-INST).

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
    FIGURE7_METRICS,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    MODEL_ORDER,
    NON_BASELINE_SCENARIO_ORDER,
    REPO_ROOT,
    SCENARIO_LABELS,
)
from seatau.plot.data_utils import load_and_prepare
from seatau.plot.plot_utils import (
    LANGUAGE_PALETTE,
    METRIC_PALETTE,
    OKABE_ITO,
    apply_style,
    despine,
    save_figure,
)

# Models shown across all conditions. Edit this list to change the subset.
# Must have data in ALL scenarios to avoid biased line means at conditions with partial coverage.
INCLUDED_MODELS: list[str] = ["gpt-5-mini", "qwen3-235b-a22b-inst", "kimi-k2.5"]
DEFAULT_ANALYSIS_DIR = REPO_ROOT / "data" / "analyses"
DEFAULT_TABLE_DIR = REPO_ROOT / "data" / "analyses"
DEFAULT_LANGUAGE_DIAGNOSTICS_DIR = REPO_ROOT / "data" / "analyses" / "language_drift_diagnostics"

LANGUAGE_FIGURE_LANGS = ["thai", "vietnamese", "filipino", "indonesian", "chinese"]
FAILURE_LABELS = {
    "wrong_write_action": "Wrong write action",
    "wrong_write_arguments_or_state": "Wrong write args/state",
    "wrong_read_arguments": "Wrong read args",
    "db_mismatch": "DB mismatch",
    "loop_or_recovery_failure": "Loop/recovery",
    "missing_required_read": "Missing read",
    "premature_final_or_incomplete_resolution": "Premature/incomplete",
}


def _allowed_models(_condition: str) -> list[str]:
    return INCLUDED_MODELS


def _build_frame(
    plot_df: pd.DataFrame,
    target_languages: list[str],
    condition_order: list[str],
) -> pd.DataFrame:
    """Combine EN Baseline rows (replicated per language) with scenario rows."""
    baseline = plot_df.loc[
        plot_df["scenario_id"].eq(1)
        & plot_df["language_key"].eq("english")
        & plot_df["language_group"].eq("language")
    ].copy()
    baseline["condition"] = "EN Baseline"

    expanded_baseline: list[pd.DataFrame] = []
    for lang in target_languages:
        copy = baseline.copy()
        copy["panel_language"] = lang
        copy["panel_label"] = LANGUAGE_LABELS.get(lang, lang)
        expanded_baseline.append(copy)

    available_scenarios = set(plot_df["scenario_id"].dropna().astype(int))
    scenarios = [s for s in NON_BASELINE_SCENARIO_ORDER if s in available_scenarios]

    lang_rows = plot_df.loc[
        plot_df["scenario_id"].isin(scenarios)
        & plot_df["language_key"].isin(target_languages)
        & plot_df["language_group"].eq("language")
    ].copy()
    lang_rows["condition"] = lang_rows["scenario_id"].map(SCENARIO_LABELS)
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

    available_scenarios = set(clean_df["scenario_id"].dropna().astype(int))
    scenarios = [s for s in NON_BASELINE_SCENARIO_ORDER if s in available_scenarios]
    condition_order = ["EN Baseline"] + [SCENARIO_LABELS[s] for s in scenarios]

    plot_df = clean_df.loc[clean_df["model_key"].isin(INCLUDED_MODELS)].copy()
    frame = _build_frame(plot_df, target_languages, condition_order)

    metric_labels = {"pass@1": "pass@1", "rho^3": r"$\rho^3$"}

    n_panels = max(1, len(target_languages))
    n_cols = min(3, n_panels)
    n_rows = math.ceil(n_panels / n_cols)
    fig = plt.figure(figsize=(2.55 * n_cols, 2.15 * n_rows))
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
            FIGURE7_METRICS, np.linspace(-0.045, 0.045, len(FIGURE7_METRICS))
        )
    }
    model_offsets = {
        m: offset
        for m, offset in zip(MODEL_ORDER, np.linspace(-0.03, 0.03, len(MODEL_ORDER)))
    }

    for ax, language in zip(axes_flat, target_languages):
        subset = frame.loc[frame["panel_language"].eq(language)]

        for metric in FIGURE7_METRICS:
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
                    edgecolor="white",
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
        # For each metric: solid line entry (mean) + faded dot entry (model avg)
        handles = []
        for m in FIGURE7_METRICS:
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


def _read_analysis_csv(analysis_dir: Path, name: str) -> pd.DataFrame:
    path = analysis_dir / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `uv run analyze-all-results --output-dir {analysis_dir}` first."
        )
    return pd.read_csv(path)


def _scenario_short(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.replace("1-english-only", "EN", regex=False)
        .str.replace("2-multilingual-tools", "L2 Tools", regex=False)
        .str.replace("3-crosslingual", "L2 Interaction", regex=False)
        .str.replace("4-translated", "L2 Domain", regex=False)
    )


def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def _refresh_crosslingual_language_correctness(
    df: pd.DataFrame,
    diagnostics_dir: Path,
) -> pd.DataFrame:
    """Replace crosslingual language correctness with refreshed turn-level values."""

    turn_path = diagnostics_dir / "contextual_turn_language.csv"
    if not turn_path.exists():
        return df

    turn_df = pd.read_csv(turn_path, low_memory=False)
    frame = turn_df.loc[
        turn_df["scenario"].eq("3-crosslingual")
        & turn_df["role"].eq("agent")
        & turn_df["counted_for_language_correctness"].astype(bool)
        & ~turn_df["is_system_error"].astype(bool)
    ].copy()
    if frame.empty:
        return df

    frame["is_target_language"] = pd.to_numeric(
        frame["is_target_language"], errors="coerce"
    ).fillna(0.0)
    run_summary = (
        frame.groupby(
            [
                "scenario",
                "domain",
                "language",
                "normalized_agent_llm",
                "simulation_source",
            ],
            dropna=False,
        )["is_target_language"]
        .mean()
        .rename("run_agent_language_correctness")
        .reset_index()
    )
    crosslingual_summary = (
        run_summary.groupby(["scenario", "domain", "language"], dropna=False)[
            "run_agent_language_correctness"
        ]
        .mean()
        .rename("mean_agent_language_correctness")
        .reset_index()
        .rename(columns={"language": "language_scenario"})
        .rename(
            columns={
                "mean_agent_language_correctness": "mean_agent_language_correctness_refreshed"
            }
        )
    )

    updated = df.merge(
        crosslingual_summary,
        on=["scenario", "domain", "language_scenario"],
        how="left",
    )
    if "mean_agent_language_correctness_refreshed" not in updated.columns:
        return updated

    refreshed = updated["mean_agent_language_correctness_refreshed"].notna()
    updated.loc[refreshed, "mean_agent_language_correctness"] = updated.loc[
        refreshed, "mean_agent_language_correctness_refreshed"
    ]
    return updated.drop(columns=["mean_agent_language_correctness_refreshed"])


def build_language_correctness_vs_performance(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Scatter agent language correctness against pass^3."""

    df = _read_analysis_csv(analysis_dir, "experiment_language_summary.csv")
    df["pass_hat_3"] = pd.to_numeric(df["pass_hat_3"], errors="coerce")
    df["agent_language_correctness"] = pd.to_numeric(
        df["agent_language_correctness"], errors="coerce"
    )
    df = _refresh_crosslingual_language_correctness(df, DEFAULT_LANGUAGE_DIAGNOSTICS_DIR)
    df = df.dropna(subset=["pass_hat_3", "agent_language_correctness"])
    scenario_order = [
        "1-english-only",
        "2-multilingual-tools",
        "3-crosslingual",
        "4-translated",
    ]
    scenario_colors = {
        "1-english-only": "#666666",
        "2-multilingual-tools": OKABE_ITO["blue"],
        "3-crosslingual": OKABE_ITO["orange"],
        "4-translated": OKABE_ITO["bluish_green"],
    }

    fig, ax = plt.subplots(figsize=(4.9, 3.25))
    for scenario in scenario_order:
        sub = df.loc[df["scenario"].eq(scenario)]
        if sub.empty:
            continue
        ax.scatter(
            sub["agent_language_correctness"],
            sub["pass_hat_3"],
            s=28,
            alpha=0.72,
            color=scenario_colors[scenario],
            edgecolor="white",
            linewidth=0.4,
            label=SCENARIO_LABELS[int(scenario[0])],
        )
    if len(df) >= 3:
        x = df["agent_language_correctness"].to_numpy(dtype=float)
        y = df["pass_hat_3"].to_numpy(dtype=float)
        fit = np.polyfit(x, y, deg=1)
        x_line = np.linspace(max(0.45, np.nanmin(x)), 1.0, 80)
        ax.plot(
            x_line,
            fit[0] * x_line + fit[1],
            color="black",
            linewidth=1.0,
            alpha=0.7,
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
    ax.set_xlabel("Mean agent language correctness")
    ax.set_ylabel("pass^3")
    ax.set_title(
        "Language correctness has weak run-level association with pass^3", pad=6
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
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.04),
        handletextpad=0.45,
        columnspacing=0.9,
        borderaxespad=0,
    )
    fig.tight_layout(rect=(0, 0.075, 1, 1), pad=0.5)
    save_figure(fig, "language_correctness_vs_pass3", fig_dir, formats)
    return fig


def build_language_drift_lollipop(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Top non-target language drift groups as a lollipop chart."""

    df = _read_analysis_csv(analysis_dir, "language_drift_by_group.csv")
    df["mean_language_correctness"] = pd.to_numeric(
        df["mean_language_correctness"], errors="coerce"
    )
    df = df.loc[
        df["role"].eq("agent") & df["non_target_lang_proportion"].notna()
    ].copy()
    df = df.loc[df["non_target_lang_proportion"].astype("string").str.len().gt(0)]
    df["non_target_share"] = 1 - df["mean_language_correctness"]
    df = df.sort_values("non_target_share", ascending=False).head(18).copy()
    df["label"] = (
        _scenario_short(df["scenario"])
        + " · "
        + df["domain"].str.title()
        + " · "
        + df["language_scenario"].map(_language_label)
        + " · "
        + df["agent_family"]
    )
    df = df.iloc[::-1]

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    y = np.arange(len(df))
    colors = [
        LANGUAGE_PALETTE.get(_language_label(lang), "#666666")
        for lang in df["language_scenario"]
    ]
    ax.hlines(y, 0, df["non_target_share"], color="#CCCCCC", linewidth=1.0)
    ax.scatter(
        df["non_target_share"], y, s=38, color=colors, edgecolor="white", linewidth=0.4
    )
    for yi, share, prop in zip(
        y, df["non_target_share"], df["non_target_lang_proportion"], strict=True
    ):
        ax.text(min(share + 0.015, 0.82), yi, str(prop), va="center", fontsize=7)
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    ax.set_xlabel("Agent non-target turn share")
    ax.set_xlim(0, max(0.6, float(df["non_target_share"].max()) + 0.12))
    ax.set_title("Largest agent language drift groups")
    ax.grid(axis="x", alpha=0.25)
    despine(ax)
    fig.tight_layout()
    save_figure(fig, "agent_language_drift_lollipop", fig_dir, formats)
    return fig


def build_failure_rate_table(analysis_dir: Path, table_dir: Path) -> pd.DataFrame:
    """Record specific failures with shares of failures and relevant trials."""

    df = _read_analysis_csv(analysis_dir, "all_trial_outcomes.csv")
    usable = df.loc[
        df["usable_for_behavioral_analysis"].astype(str).str.lower().eq("true")
    ].copy()
    failures = usable.loc[
        usable["is_failed_or_partial"].astype(str).str.lower().eq("true")
    ].copy()
    group_cols = ["scenario", "domain", "normalized_agent_llm", "language_scenario"]
    rows = []

    def add_group(group_name: str, group_cols_inner: list[str]) -> None:
        if group_cols_inner:
            relevant = usable.groupby(group_cols_inner).size().rename("relevant_trials")
            failure_totals = (
                failures.groupby(group_cols_inner).size().rename("total_failures")
            )
            specific = (
                failures.groupby([*group_cols_inner, "primary_label"])
                .size()
                .rename("failure_count")
                .reset_index()
            )
            merged = specific.merge(
                relevant.reset_index(), on=group_cols_inner, how="left"
            ).merge(failure_totals.reset_index(), on=group_cols_inner, how="left")
        else:
            merged = (
                failures.groupby("primary_label")
                .size()
                .rename("failure_count")
                .reset_index()
            )
            merged["relevant_trials"] = len(usable)
            merged["total_failures"] = len(failures)
        merged["summary_level"] = group_name
        rows.append(merged)

    add_group("overall", [])
    add_group("scenario", ["scenario"])
    add_group("scenario_domain", ["scenario", "domain"])
    add_group("scenario_domain_model_language", group_cols)

    table = pd.concat(rows, ignore_index=True)
    table["failure_pct_of_all_failures"] = (
        table["failure_count"] / table["total_failures"]
    )
    table["failure_pct_of_relevant_trials"] = (
        table["failure_count"] / table["relevant_trials"]
    )
    table["failure_label"] = (
        table["primary_label"].map(FAILURE_LABELS).fillna(table["primary_label"])
    )
    table = table.sort_values(
        ["summary_level", "failure_pct_of_relevant_trials", "failure_count"],
        ascending=[True, False, False],
    )

    table_dir.mkdir(parents=True, exist_ok=True)
    out_csv = table_dir / "specific_failure_rates.csv"
    table.to_csv(out_csv, index=False)

    top = table.loc[table["summary_level"].eq("scenario_domain_model_language")].head(
        80
    )
    out_md = table_dir / "specific_failure_rates_top.md"
    lines = [
        "# Specific Failure Rates",
        "",
        "Percentages are computed within each relevant group.",
        "",
        "| scenario | domain | model | language | failure | count | % failures | % relevant trials |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in top.itertuples(index=False):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(getattr(row, "scenario", "")),
                    str(getattr(row, "domain", "")),
                    str(getattr(row, "normalized_agent_llm", "")),
                    str(getattr(row, "language_scenario", "")),
                    str(getattr(row, "failure_label", "")),
                    f"{int(getattr(row, 'failure_count'))}",
                    f"{getattr(row, 'failure_pct_of_all_failures'):.1%}",
                    f"{getattr(row, 'failure_pct_of_relevant_trials'):.1%}",
                ]
            )
            + " |"
        )
    out_md.write_text("\n".join(lines))
    print(f"Wrote failure tables:\n  {out_csv}\n  {out_md}")
    return table


def build_failure_mode_share_figure(
    failure_table: pd.DataFrame,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Visualize specific failure shares by scenario/domain."""

    df = failure_table.loc[failure_table["summary_level"].eq("scenario_domain")].copy()
    keep = [
        "wrong_write_action",
        "wrong_write_arguments_or_state",
        "wrong_read_arguments",
        "db_mismatch",
        "loop_or_recovery_failure",
        "missing_required_read",
    ]
    df = df.loc[df["primary_label"].isin(keep)]
    df["group"] = _scenario_short(df["scenario"]) + "\n" + df["domain"].str.title()
    pivot = (
        df.pivot_table(
            index="group",
            columns="primary_label",
            values="failure_pct_of_relevant_trials",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=keep, fill_value=0)
        .sort_index()
    )
    colors = [
        OKABE_ITO["blue"],
        OKABE_ITO["vermillion"],
        OKABE_ITO["orange"],
        OKABE_ITO["bluish_green"],
        OKABE_ITO["reddish_purple"],
        "#777777",
    ]

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    bottom = np.zeros(len(pivot))
    x = np.arange(len(pivot))
    for label, color in zip(keep, colors, strict=True):
        vals = pivot[label].to_numpy(dtype=float)
        ax.bar(
            x, vals, bottom=bottom, width=0.72, color=color, label=FAILURE_LABELS[label]
        )
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")
    ax.set_ylabel("Failures as share of usable trials")
    ax.set_title("Specific failure modes by scenario and domain")
    ax.legend(ncol=3, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.18))
    ax.grid(axis="y", alpha=0.25)
    despine(ax)
    fig.tight_layout()
    save_figure(fig, "specific_failure_mode_share", fig_dir, formats)
    return fig


def build_language_rank_slopegraph(
    analysis_dir: Path,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    """Show pass@3 and agent language correctness by domain."""

    df = _read_analysis_csv(analysis_dir, "language_passhat_summary.csv")
    df = df.loc[df["language_scenario"].isin(LANGUAGE_FIGURE_LANGS)].copy()
    df["mean_pass_hat_3"] = pd.to_numeric(df["mean_pass_hat_3"], errors="coerce")
    df["mean_agent_language_correctness"] = pd.to_numeric(
        df["mean_agent_language_correctness"], errors="coerce"
    )
    df = df.dropna(subset=["mean_pass_hat_3", "mean_agent_language_correctness"])
    scenario_order = ["2-multilingual-tools", "3-crosslingual", "4-translated"]
    domains = ["airline", "retail", "telecom"]
    fig = plt.figure(figsize=(9.4, 3.7), constrained_layout=True)
    grid = fig.add_gridspec(
        1, len(domains) + 1, width_ratios=[1, 1, 1, 0.035], wspace=0.08
    )
    axes = [fig.add_subplot(grid[0, idx]) for idx in range(len(domains))]
    cax = fig.add_subplot(grid[0, len(domains)])
    for ax, domain in zip(axes, domains, strict=True):
        sub = df.loc[df["domain"].eq(domain)].copy()
        pivot = sub.pivot_table(
            index="scenario",
            columns="language_scenario",
            values="mean_pass_hat_3",
            aggfunc="mean",
        ).reindex(index=scenario_order, columns=LANGUAGE_FIGURE_LANGS)
        lang_correctness = sub.pivot_table(
            index="scenario",
            columns="language_scenario",
            values="mean_agent_language_correctness",
            aggfunc="mean",
        ).reindex(index=scenario_order, columns=LANGUAGE_FIGURE_LANGS)
        data = pivot.to_numpy(dtype=float)
        im = ax.imshow(data, vmin=0.10, vmax=0.65, cmap="magma_r", aspect="auto")
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                pass_value = data[i, j]
                lang_value = lang_correctness.to_numpy(dtype=float)[i, j]
                if np.isnan(pass_value):
                    continue
                text_color = "white" if pass_value < 0.28 else "black"
                ax.text(
                    j,
                    i,
                    f"p {pass_value:.2f}\nlc {lang_value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=6.3,
                    color=text_color,
                )
        ax.set_xticks(np.arange(len(LANGUAGE_FIGURE_LANGS)))
        ax.set_xticklabels([_language_label(lang) for lang in LANGUAGE_FIGURE_LANGS])
        ax.set_yticks(np.arange(len(scenario_order)))
        ax.set_yticklabels([SCENARIO_LABELS[int(s[0])] for s in scenario_order])
        ax.set_title(domain.title())
        ax.tick_params(length=0)
        despine(ax)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Mean pass@3")
    fig.suptitle("Low pass@3 often occurs despite high agent language correctness")
    save_figure(fig, "language_correctness_pass3_by_domain", fig_dir, formats)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    parser.add_argument(
        "--skip-all-results",
        action="store_true",
        help="Only build the original language degradation figure from experiments_all.csv.",
    )
    args = parser.parse_args()

    apply_style()
    _, _, clean_df, duplicate_summary, audit = load_and_prepare(args.csv)

    print("Audit:")
    for k, v in audit.items():
        print(f"  {k}: {v}")
    if not duplicate_summary.empty:
        print(f"\nDuplicate groups resolved ({len(duplicate_summary)}):")
        print(duplicate_summary.to_string(index=False))

    build_language_degradation(clean_df, args.output_dir, tuple(args.formats))
    if not args.skip_all_results:
        build_language_correctness_vs_performance(
            args.analysis_dir, args.output_dir, tuple(args.formats)
        )
        build_language_drift_lollipop(
            args.analysis_dir, args.output_dir, tuple(args.formats)
        )
        build_language_rank_slopegraph(
            args.analysis_dir, args.output_dir, tuple(args.formats)
        )
        failure_table = build_failure_rate_table(args.analysis_dir, args.table_dir)
        build_failure_mode_share_figure(
            failure_table, args.output_dir, tuple(args.formats)
        )
    plt.close("all")


if __name__ == "__main__":
    main()
