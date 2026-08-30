"""Plot critical and benign error shares by setting and role.

Bars omit correct outcomes so height reads as total error share. Outcome rows use
simulation denominators; tag rows use turn denominators.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from paths import ERROR_TAG_RATES_CSV
from seatau.plot.style import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    PLOT_FIGSIZE_TWO_COL_TALL,
    PLOT_LABEL_SIZE,
    PLOT_LEGEND_SIZE,
    PLOT_TITLE_SIZE,
    SEA_COLORS,
    apply_style,
    save_figure,
)

FIGURE_STEM = "error_breakdown_by_setting_role"

# Outcome rows use `minor` for the figure's benign-severity label.
_SEVERITY_COLUMN = {"critical": "critical", "benign": "minor", "correct": "correct"}


def load_error_breakdown(csv_path: Path = ERROR_TAG_RATES_CSV) -> pd.DataFrame:
    """Build the outcome-share table consumed by ``build_figure``.

    Shares are averaged across domains for each setting/language pair.
    """
    df = pd.read_csv(csv_path)
    outcome = df.loc[df["category"] == "outcome"].copy()
    outcome["rate"] = 100.0 * outcome["count"] / outcome["total_sims"]
    outcome["language"] = outcome["language"].str.lower()

    per_lang = outcome.groupby(
        ["setting", "language", "role", "severity"], as_index=False
    )["rate"].mean()
    per_lang["column"] = (
        per_lang["role"] + "_" + per_lang["severity"].map(_SEVERITY_COLUMN)
    )
    wide = per_lang.pivot_table(
        index=["setting", "language"], columns="column", values="rate"
    ).reset_index()
    return wide


def _as_proportions(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    out[columns] = out[columns].apply(pd.to_numeric, errors="coerce")
    if out[columns].to_numpy().max() > 1:
        out[columns] = out[columns] / 100.0
    return out


def _normalize_parts(frame: pd.DataFrame, columns: list[str]) -> None:
    totals = frame[columns].sum(axis=1).replace(0, np.nan)
    frame[columns] = frame[columns].div(totals, axis=0)


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the paired vertical stacked-bar error-share figure.

    Each panel covers one role; non-English settings are adjacent bars and the
    English baseline is shown with critical and total-error reference lines.
    """

    required_cols = [
        "language",
        "setting",
        "agent_critical",
        "agent_minor",
        "agent_correct",
        "user_critical",
        "user_minor",
        "user_correct",
    ]
    plot_df = _as_proportions(df.loc[:, required_cols], required_cols[2:])
    _normalize_parts(plot_df, ["agent_critical", "agent_minor", "agent_correct"])
    _normalize_parts(plot_df, ["user_critical", "user_minor", "user_correct"])

    settings = ["L2 Interaction", "L2 Tool", "L2 Domain"]
    who_list = ["agent", "user"]
    who_titles = {"agent": "Agent", "user": "User"}
    parts = ["critical", "minor"]
    hatches = {
        "L2 Interaction": "",
        "L2 Tool": "xx",
        "L2 Domain": "///",
    }
    preferred_order = [
        "vietnamese",
        "chinese",
        "indonesian",
        "filipino",
        "thai",
    ]
    available = set(plot_df["language"])
    lang_order = [lang for lang in preferred_order if lang in available]
    lang_order.extend(
        lang
        for lang in plot_df["language"].unique()
        if lang not in lang_order and lang != "english"
    )
    n_lang = len(lang_order)

    # Severity colors: red for critical, yellow for benign.
    colors = {
        "critical": SEA_COLORS["red"],
        "minor": SEA_COLORS["yellow"],
    }
    crit_line_color = SEA_COLORS["red"]
    total_line_color = SEA_COLORS["yellow"]
    crit_ls = (0, (5.0, 2.5))
    total_ls = "-."
    bar_width = 0.24
    pair_gap = 0.02
    group_positions = np.arange(n_lang, dtype=float)
    offsets = {
        "L2 Interaction": -(bar_width + pair_gap),
        "L2 Tool": 0.0,
        "L2 Domain": (bar_width + pair_gap),
    }

    fig, axes = plt.subplots(
        1, 2, figsize=(PLOT_FIGSIZE_TWO_COL_TALL[0], 3.55), sharey=True
    )

    en_row = plot_df.loc[
        plot_df["setting"].eq("English Baseline") & plot_df["language"].eq("english")
    ]

    for i, who in enumerate(who_list):
        ax = axes[i]

        for setting_name in settings:
            sub = plot_df.loc[
                plot_df["setting"].eq(setting_name)
                & plot_df["language"].isin(lang_order)
            ].copy()
            sub["language"] = pd.Categorical(
                sub["language"], categories=lang_order, ordered=True
            )
            sub = sub.sort_values("language").set_index("language").reindex(lang_order)

            x = group_positions + offsets[setting_name]
            bottom = np.zeros(n_lang)
            for part in parts:
                vals = sub[f"{who}_{part}"].to_numpy()
                ax.bar(
                    x,
                    vals,
                    bottom=bottom,
                    width=bar_width,
                    color=colors[part],
                    alpha=1.0,
                    edgecolor=SEA_COLORS["black"],
                    linewidth=0.4,
                    hatch=hatches[setting_name],
                    zorder=3,
                )
                bottom += vals

        if not en_row.empty:
            ref_crit = en_row[f"{who}_critical"].values[0]
            ref_minor = en_row[f"{who}_minor"].values[0]
            ref_total = ref_crit + ref_minor
            ax.axhline(
                ref_crit,
                color=crit_line_color,
                linestyle=crit_ls,
                linewidth=1.3,
                zorder=4,
            )
            ax.axhline(
                ref_total,
                color=total_line_color,
                linestyle=total_ls,
                linewidth=1.4,
                zorder=4,
            )

            text_str = (
                f"EN Critical: {ref_crit:.1%}\n"
                f"EN Total: {ref_total:.1%}\n"
                f"(Benign: {ref_minor:.1%})"
            )
            ax.text(
                0.98,
                0.96,
                text_str,
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=PLOT_LABEL_SIZE - 1.0,
                color=SEA_COLORS["black"],
                linespacing=1.15,
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="white",
                    alpha=0.9,
                    edgecolor="#cccccc",
                    linewidth=0.5,
                ),
                zorder=5,
            )

        ax.set_title(who_titles[who], fontsize=PLOT_TITLE_SIZE)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
        ax.tick_params(axis="both", labelsize=PLOT_LABEL_SIZE)
        ax.set_xticks(
            group_positions,
            [LANGUAGE_LABELS.get(lang, lang) for lang in lang_order],
        )
        ax.grid(axis="y", color="#dddddd", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        if i == 0:
            ax.set_ylabel(
                "Share of simulations with an error", fontsize=PLOT_LABEL_SIZE
            )
        else:
            ax.tick_params(axis="y", length=0)

    ymax = max(ax.get_ylim()[1] for ax in axes)
    for ax in axes:
        ax.set_ylim(0, ymax * 1.20)

    outcome_handles = [
        Patch(
            facecolor=colors["critical"],
            edgecolor=SEA_COLORS["black"],
            linewidth=0.4,
            label="Critical",
        ),
        Patch(
            facecolor=colors["minor"],
            edgecolor=SEA_COLORS["black"],
            linewidth=0.4,
            label="Benign",
        ),
    ]
    ref_handles = [
        Line2D(
            [0],
            [0],
            color=crit_line_color,
            linestyle=crit_ls,
            linewidth=1.3,
            label="EN Critical",
        ),
        Line2D(
            [0],
            [0],
            color=total_line_color,
            linestyle=total_ls,
            linewidth=1.4,
            label="EN Total Error",
        ),
    ]
    setting_handles = [
        Patch(
            facecolor="white",
            edgecolor=SEA_COLORS["black"],
            linewidth=0.6,
            hatch=hatches[setting_name],
            label=setting_name,
        )
        for setting_name in settings
    ]

    all_left_handles = outcome_handles + ref_handles
    fig.legend(
        handles=all_left_handles,
        ncol=len(all_left_handles),
        loc="lower center",
        fontsize=PLOT_LEGEND_SIZE,
        bbox_to_anchor=(0.33, 0.015),
        columnspacing=0.8,
        handletextpad=0.3,
    )
    fig.legend(
        handles=setting_handles,
        ncol=len(setting_handles),
        loc="lower center",
        fontsize=PLOT_LEGEND_SIZE,
        bbox_to_anchor=(0.78, 0.015),
        columnspacing=0.8,
        handletextpad=0.3,
    )
    fig.add_artist(
        Line2D(
            [0.585, 0.585],
            [0.02, 0.09],
            transform=fig.transFigure,
            color="#b3b3b3",
            linewidth=0.8,
        )
    )
    fig.subplots_adjust(left=0.08, right=0.985, top=0.91, bottom=0.22, wspace=0.15)
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ERROR_TAG_RATES_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    outputs = save_figure(
        build_figure(load_error_breakdown(args.csv)),
        FIGURE_STEM,
        args.output_dir,
        tuple(args.formats),
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
