"""Tool-language scaling: pass@1 and rho^3 vs. number of tool languages.

Single line chart showing how performance changes as tool-language count increases
from 1 (English-only, scenario 1) to 5 (5-language tool mix, scenario 2).

X-axis:  number of tool languages (1–5)
Y-axis:  score
Lines:   pass@1 and rho^3, each averaged across all available models × domains
Error bars: SEM across models × domains
Dots:    per-model averages (one dot per model per x-position, same color as the line)

Usage:
    python -m seatau.plot.tool_mix_scaling
    python -m seatau.plot.tool_mix_scaling --csv path/to/data.csv --output-dir path/to/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from seatau.plot.config import (
    DEFAULT_CSV_PATH,
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    MODEL_ORDER,
    SEA_COLOR_SEQUENCE,
    SEA_COLORS,
)
from seatau.plot.plot_utils import apply_style, despine, load_and_prepare, save_figure

METRICS = ["pass@1", "rho^3"]
METRIC_LABELS = {"pass@1": "pass@1", "rho^3": r"$\rho^3$"}
METRIC_PALETTE = {
    "pass@1": SEA_COLOR_SEQUENCE[0],
    "rho^3": SEA_COLOR_SEQUENCE[1],
}
PLOT_MODEL_KEYS = ["gpt-5-mini", "qwen-3-235b-it"]

# x-axis tick labels and their corresponding (scenario_id, language_key) lookups
_X_TICKS = [1, 2, 3, 4, 5]
_X_CONDITIONS: dict[int, tuple[int, str]] = {
    1: (1, "english"),
    2: (2, "tool_mix_2"),
    3: (2, "tool_mix_3"),
    4: (2, "tool_mix_4"),
    5: (2, "tool_mix_5"),
}


def _condition_rows(
    clean_df: pd.DataFrame, scenario_id: int, language_key: str, models: list[str]
) -> pd.DataFrame:
    return clean_df.loc[
        clean_df["scenario_id"].eq(scenario_id)
        & clean_df["language_key"].eq(language_key)
        & clean_df["model_key"].isin(models)
    ].copy()


def build_tool_mix_scaling(
    clean_df: pd.DataFrame,
    fig_dir: Path,
    formats: tuple[str, ...] = EXPORT_FORMATS,
) -> plt.Figure:
    available_lang_keys = set(clean_df["language_key"])
    x_ticks = [x for x in _X_TICKS if _X_CONDITIONS[x][1] in available_lang_keys]

    models = [m for m in PLOT_MODEL_KEYS if m in set(clean_df["model_key"])]
    model_offsets = {
        m: offset
        for m, offset in zip(MODEL_ORDER, np.linspace(-0.06, 0.06, len(MODEL_ORDER)))
    }
    metric_offsets = {
        m: offset for m, offset in zip(METRICS, np.linspace(-0.03, 0.03, len(METRICS)))
    }

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    for metric in METRICS:
        means, sems, dot_rows_list = [], [], []

        for x in x_ticks:
            scenario_id, language_key = _X_CONDITIONS[x]
            rows = _condition_rows(clean_df, scenario_id, language_key, models)
            vals = rows[metric].dropna()
            means.append(vals.mean() if len(vals) else np.nan)
            sems.append(vals.std() / np.sqrt(len(vals)) if len(vals) > 1 else 0.0)

            # per-model averages (across domains) for dots
            dot_rows_list.append(
                rows.groupby("model_key")[metric].mean().reindex(models).reset_index()
            )

        y = np.array(means, dtype=float)
        ye = np.array(sems, dtype=float)
        ye[np.isnan(y)] = np.nan

        # model dots
        for x_idx, (x, dot_rows) in enumerate(zip(x_ticks, dot_rows_list)):
            for _, row in dot_rows.dropna(subset=[metric]).iterrows():
                dot_x = (
                    x + metric_offsets[metric] + model_offsets.get(row["model_key"], 0)
                )
                ax.scatter(
                    dot_x,
                    row[metric],
                    s=22,
                    color=METRIC_PALETTE[metric],
                    edgecolor=SEA_COLORS["white"],
                    linewidth=0.4,
                    alpha=0.75,
                    zorder=4,
                )

        ax.errorbar(
            x_ticks,
            y,
            yerr=ye,
            marker="o",
            markersize=5,
            linewidth=1.8,
            capsize=3,
            color=METRIC_PALETTE[metric],
            label=METRIC_LABELS[metric],
            zorder=3,
        )

    ax.set_xlabel("Number of languages for translated tools")
    ax.set_ylabel("Score")
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([str(x) for x in x_ticks])
    ax.set_ylim(0, 0.85)
    ax.grid(axis="y", alpha=0.35)
    despine(ax)

    handles = [
        Line2D(
            [0],
            [0],
            color=METRIC_PALETTE[m],
            marker="o",
            markersize=4,
            linewidth=1.8,
            label=METRIC_LABELS[m],
        )
        for m in METRICS
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
        frameon=False,
        handlelength=1.4,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.90])
    save_figure(fig, "perf_tool_mix", fig_dir, formats)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    args = parser.parse_args()

    apply_style()
    _, _, clean_df, duplicate_summary, audit = load_and_prepare(args.csv)

    print("Audit:")
    for k, v in audit.items():
        print(f"  {k}: {v}")
    if not duplicate_summary.empty:
        print(f"\nDuplicate groups resolved ({len(duplicate_summary)}):")
        print(duplicate_summary.to_string(index=False))

    build_tool_mix_scaling(clean_df, args.output_dir, tuple(args.formats))
    plt.close("all")


if __name__ == "__main__":
    main()
