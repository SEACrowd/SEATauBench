"""Plot critical, benign, and correct outcome shares by setting and role."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
    PLOT_FIGSIZE_TWO_COL_TALL,
    PLOT_LABEL_SIZE,
    PLOT_LEGEND_SIZE,
    PLOT_TITLE_SIZE,
    SEA_COLORS,
)
from seatau.plot.plot_utils import (
    INTERACTION_RECAP_PATH,
    apply_style,
    read_interaction_recap,
    save_figure,
)

FIGURE_STEM = "error_breakdown_by_setting_role"


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
    """Build the paired stacked horizontal bar figure.

    Layout: two panels (Agent, User) so the role split is the primary
    grouping. Within each panel every language gets an adjacent pair of
    stacked bars -- solid for L2 Interaction, hatched for L2 Domain -- so
    the scenario comparison is a direct neighboring-bar read rather than a
    separate panel.
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
    agent_cols = ["agent_critical", "agent_minor", "agent_correct"]
    user_cols = ["user_critical", "user_minor", "user_correct"]
    _normalize_parts(plot_df, agent_cols)
    _normalize_parts(plot_df, user_cols)

    settings = ["L2 Interaction", "L2 Domain"]
    who_list = ["agent", "user"]
    who_titles = {"agent": "Agent", "user": "User"}
    parts = ["critical", "minor", "correct"]
    hatches = {"L2 Interaction": "", "L2 Domain": "///"}
    base = plot_df.loc[plot_df["setting"].eq("L2 Domain")].copy()
    if base.empty:
        base = plot_df.copy()
    if "english" in base["language"].values:
        others = (
            base.loc[base["language"].ne("english"), ["language", "agent_correct"]]
            .sort_values("agent_correct", ascending=False)["language"]
            .tolist()
        )
        lang_order = ["english", *others]
    else:
        lang_order = base.sort_values("agent_correct", ascending=False)[
            "language"
        ].tolist()
    n_lang = len(lang_order)

    colors = {
        "critical": SEA_COLORS["blue"],
        "minor": SEA_COLORS["red"],
        "correct": SEA_COLORS["yellow"],
    }

    bar_height = 0.36
    pair_gap = 0.02
    group_positions = np.arange(n_lang, dtype=float)
    offsets = {
        "L2 Interaction": bar_height / 2 + pair_gap / 2,
        "L2 Domain": -(bar_height / 2 + pair_gap / 2),
    }

    fig, axes = plt.subplots(
        1, 2, figsize=PLOT_FIGSIZE_TWO_COL_TALL, sharex=True, sharey=False
    )

    for i, who in enumerate(who_list):
        ax = axes[i]
        for setting_name in settings:
            sub = plot_df.loc[plot_df["setting"].eq(setting_name)].copy()
            sub["language"] = pd.Categorical(
                sub["language"], categories=lang_order, ordered=True
            )
            sub = sub.sort_values("language").set_index("language").reindex(lang_order)
            y = group_positions + offsets[setting_name]
            left = np.zeros(n_lang)
            for part in parts:
                vals = sub[f"{who}_{part}"].to_numpy()
                ax.barh(
                    y,
                    vals,
                    left=left,
                    height=bar_height,
                    color=colors[part],
                    alpha=0.85,
                    edgecolor=SEA_COLORS["black"],
                    linewidth=0.4,
                    hatch=hatches[setting_name],
                    label="Benign" if part == "minor" else part.capitalize(),
                )
                left += vals

            if "english" in sub.index and setting_name == "L2 Interaction":
                ref_critical = sub.loc["english", f"{who}_critical"]
                if not np.isnan(ref_critical):
                    ax.axvline(
                        ref_critical,
                        color=colors["critical"],
                        linestyle="--",
                        linewidth=1.4,
                    )
                    ax.text(
                        ref_critical - 0.1,
                        1.0,
                        f"{ref_critical:.1%}",
                        transform=ax.get_xaxis_transform(),
                        ha="center",
                        va="bottom",
                        fontsize=PLOT_LABEL_SIZE,
                        color=colors["critical"],
                        fontweight="bold",
                    )

        ax.set_title(who_titles[who], fontsize=PLOT_TITLE_SIZE)
        ax.set_xlim(0, 1.0)
        ax.set_xticks(np.linspace(0, 1, 6))
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
        ax.tick_params(axis="x", labelsize=PLOT_LABEL_SIZE)
        ax.set_ylim(-0.65, n_lang - 0.35)
        for gy in group_positions[:-1]:
            ax.axhline(gy + 0.5, color=SEA_COLORS["black"], linewidth=0.4, alpha=0.25)
        if i == 0:
            ax.set_yticks(
                group_positions,
                [LANGUAGE_LABELS.get(lang, lang) for lang in lang_order],
                fontsize=PLOT_LABEL_SIZE,
            )
        else:
            ax.set_yticks(group_positions, ["" for _ in group_positions])
            ax.tick_params(axis="y", length=0)

    outcome_handles = [
        Patch(
            facecolor=colors[part],
            alpha=0.85,
            edgecolor=SEA_COLORS["black"],
            linewidth=0.4,
            label="Benign" if part == "minor" else part.capitalize(),
        )
        for part in parts
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
    fig.legend(
        handles=[*outcome_handles, *setting_handles],
        ncol=len(outcome_handles) + len(setting_handles),
        loc="lower center",
        fontsize=PLOT_LEGEND_SIZE,
        bbox_to_anchor=(0.5, 0.0),
        columnspacing=1.2,
        handletextpad=0.5,
    )
    fig.subplots_adjust(left=0.055, right=0.985, top=0.95, bottom=0.135, wspace=0.15)
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recap", type=Path, default=INTERACTION_RECAP_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    outputs = save_figure(
        build_figure(read_interaction_recap(args.recap)),
        FIGURE_STEM,
        args.output_dir,
        tuple(args.formats),
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
