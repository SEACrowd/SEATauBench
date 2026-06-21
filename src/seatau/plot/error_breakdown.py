"""Plot critical, benign, and correct outcome shares by setting and role."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from seatau.plot.config import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    LANGUAGE_LABELS,
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
    for col in columns:
        out[col] = pd.to_numeric(
            out[col].astype("string").str.replace("%", "", regex=False),
            errors="coerce",
        )
    if out[columns].max().max() > 1:
        out[columns] = out[columns] / 100.0
    return out


def _normalize_parts(frame: pd.DataFrame, columns: list[str]) -> None:
    totals = frame[columns].sum(axis=1).replace(0, np.nan)
    frame[columns] = frame[columns].div(totals, axis=0)


def build_figure(df: pd.DataFrame) -> plt.Figure:
    """Build the stacked horizontal bar figure."""

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
    parts = ["critical", "minor", "correct"]
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

    colors = {
        "critical": SEA_COLORS["blue"],
        "minor": SEA_COLORS["red"],
        "correct": SEA_COLORS["yellow"],
    }
    fig, axes = plt.subplots(1, 4, figsize=(18, 5), sharex=True, sharey=True)
    y_centers = np.arange(len(lang_order))

    for i, (setting_name, who) in enumerate((s, w) for s in settings for w in who_list):
        ax = axes[i]
        sub = plot_df.loc[plot_df["setting"].eq(setting_name)].copy()
        sub["language"] = pd.Categorical(
            sub["language"], categories=lang_order, ordered=True
        )
        sub = sub.sort_values("language").set_index("language").reindex(lang_order)
        left = np.zeros(len(lang_order))
        for part in parts:
            vals = sub[f"{who}_{part}"].to_numpy()
            ax.barh(
                y_centers,
                vals,
                left=left,
                color=colors[part],
                alpha=0.5,
                edgecolor=SEA_COLORS["black"],
                linewidth=0.5,
                label="Benign" if part == "minor" else part.capitalize(),
            )
            left += vals

        if "english" in sub.index:
            ref_critical = sub.loc["english", f"{who}_critical"]
            if not np.isnan(ref_critical):
                ax.axvline(
                    ref_critical,
                    color=colors["critical"],
                    linestyle="--",
                    linewidth=2.0,
                )
                ax.text(
                    ref_critical - 0.1,
                    0.95,
                    f"{ref_critical:.1%}",
                    transform=ax.get_xaxis_transform(),
                    ha="center",
                    va="bottom",
                    fontsize=PLOT_LABEL_SIZE,
                    color=colors["critical"],
                    fontweight="bold",
                )

        ax.set_title(f"{setting_name} - {who.capitalize()}", fontsize=PLOT_TITLE_SIZE)
        ax.set_xlim(0, 1.0)
        ax.set_xticks(np.linspace(0, 1, 6))
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
        ax.set_yticks(
            y_centers,
            [LANGUAGE_LABELS.get(lang, lang) for lang in lang_order],
            fontsize=PLOT_LABEL_SIZE,
        )
        ax.tick_params(axis="x", labelsize=PLOT_LABEL_SIZE)

    handles, labels = axes[0].get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    fig.legend(
        uniq.values(),
        uniq.keys(),
        ncol=3,
        loc="lower center",
        fontsize=PLOT_LEGEND_SIZE,
        bbox_to_anchor=(0.5, 0.01),
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.98))
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
