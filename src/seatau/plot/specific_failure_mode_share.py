"""Specific failure mode share by scenario and domain."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from seatau.constants import FAILURE_MODE_DIR
from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    PLOT_FIGSIZE_TWO_COL_TALL,
    SCENARIO_ORDER,
    SEA_COLORS,
)
from seatau.plot.language_degradation_shared import (
    FAILURE_LABELS,
    _read_analysis_csv,
    _scenario_short,
)
from seatau.plot.plot_utils import (
    apply_style,
    despine,
    normalize_scenario_id_series,
    save_figure,
)


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
    scenario_rank = {scenario: idx for idx, scenario in enumerate(SCENARIO_ORDER)}
    df["scenario_rank"] = (
        normalize_scenario_id_series(df["scenario"])
        .map(scenario_rank)
        .fillna(len(scenario_rank))
    )
    ordered_groups = (
        df.drop_duplicates("group")
        .sort_values(["scenario_rank", "domain"])["group"]
        .tolist()
    )
    pivot = df.pivot_table(
        index="group",
        columns="primary_label",
        values="failure_pct_of_relevant_trials",
        aggfunc="sum",
        fill_value=0,
    ).reindex(index=ordered_groups, columns=keep, fill_value=0)
    colors = [
        SEA_COLORS["blue"],
        SEA_COLORS["red"],
        SEA_COLORS["yellow"],
        SEA_COLORS["black"],
        SEA_COLORS["red"],
        SEA_COLORS["black"],
    ]

    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE_TWO_COL_TALL)
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
    ax.set_title("Specific failure modes by scenario and domain", y=1.32)
    ax.legend(ncol=3, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.20))
    ax.grid(axis="y", alpha=0.25)
    despine(ax)
    fig.tight_layout()
    save_figure(fig, "specific_failure_mode_share", fig_dir, formats)
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, default=FAILURE_MODE_DIR)
    parser.add_argument("--table-dir", type=Path, default=FAILURE_MODE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    failure_table = build_failure_rate_table(args.analysis_dir, args.table_dir)
    build_failure_mode_share_figure(failure_table, args.output_dir, tuple(args.formats))
    plt.close("all")


if __name__ == "__main__":
    main()
