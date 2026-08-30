"""Plot average error-tag occurrences per 100 role turns.

The module reads tidy review data, averages rates across domains and languages,
and writes one all-tag figure plus a top-tag agent figure.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from paths import ERROR_TAG_RATES_CSV
from seatau.analysis.error_tag_rates import TAG_LABEL, TAGS
from seatau.plot.style import (
    DEFAULT_FIG_DIR,
    EXPORT_FORMATS,
    PLOT_COLUMN_WIDTH,
    PLOT_TWO_COLUMN_WIDTH,
    SEA_COLORS,
    apply_style,
    save_figure,
)

ROLE_TAG_RATES_STEM = "avg_error_tags_occ_per_100_turns"
AGENT_TAG_RATES_STEM = "avg_error_tags_occ_agent"

SETTINGS = ["English Baseline", "L2 Interaction", "L2 Tool", "L2 Domain"]

# Tags below this threshold are omitted from the main-text figure.
PLOT_THRESHOLD = 0.01

# Explicit sizes keep the dense panels readable.
FS_TICK, FS_LABEL, FS_TITLE, FS_LEGEND = 6.0, 6.5, 8.0, 6.0

# Severity uses red/yellow; scenario identity uses hue and hatch.
OUTCOME_COLORS = {
    "critical": SEA_COLORS["red"],
    "benign": SEA_COLORS["yellow"],
}
CRIT_COLOR = OUTCOME_COLORS["critical"]
BEN_COLOR = OUTCOME_COLORS["benign"]
EDGE = SEA_COLORS["black"]
SCENARIO_ALPHA = [1.0, 1.0, 1.0, 1.0]

# Scenario colors match the other scenario-comparison figures.
SCENARIO_COLORS = {
    "English Baseline": SEA_COLORS["green"],
    "L2 Interaction": SEA_COLORS["yellow"],
    "L2 Tool": SEA_COLORS["blue"],
    "L2 Domain": SEA_COLORS["red"],
}
SEVERITY_ALPHA = {"crit": 1.0, "benign": 1.0}
SEVERITY_HATCH = {"crit": "", "benign": "///"}
# Backslash hatch is more legible at this bar thickness.
SCENARIO_HATCHES = ("", "//", "\\", "xx")
DEFAULT_TOP_N = 10


def load_data(csv_path: Path) -> pd.DataFrame:
    """Read tidy error-tag rows, excluding per-simulation outcome rows."""
    df = pd.read_csv(csv_path)
    return df.loc[df["category"].isin(TAGS)].copy()


def aggregate(df: pd.DataFrame) -> dict[tuple[str, str, str, str], float]:
    """Average per-turn rates across domains, then languages."""
    working = df.copy()
    working["rate"] = np.where(
        working["turns"] > 0,
        100.0 * working["count"] / working["turns"],
        0.0,
    )
    per_language = working.groupby(
        ["setting", "role", "category", "severity", "language"], as_index=False
    )["rate"].mean()
    per_setting = per_language.groupby(["setting", "role", "category", "severity"])[
        "rate"
    ].mean()

    out: dict[tuple[str, str, str, str], float] = defaultdict(float)
    for (setting, role, tag, severity), value in per_setting.items():
        bucket = "crit" if severity == "critical" else "benign"
        out[(setting, role, tag, bucket)] = value
    return out


def tags_for(agg: dict, role: str, threshold: float) -> tuple[list[str], list[str]]:
    """Return tags meeting the threshold, ranked by L2 Domain total."""
    keep = [
        t
        for t in TAGS
        if max(
            agg[(s, role, t, "crit")] + agg[(s, role, t, "benign")] for s in SETTINGS
        )
        >= threshold
    ]
    keep.sort(
        key=lambda t: (
            -(
                agg[("L2 Domain", role, t, "crit")]
                + agg[("L2 Domain", role, t, "benign")]
            )
        )
    )
    dropped = [t for t in TAGS if t not in keep]
    return keep, dropped


def top_tags(agg: dict, role: str, n: int) -> list[str]:
    """Return the top ``n`` tags by L2 Domain total."""
    ranked = sorted(
        TAGS,
        key=lambda t: (
            -(
                agg[("L2 Domain", role, t, "crit")]
                + agg[("L2 Domain", role, t, "benign")]
            )
        ),
    )
    return ranked[:n]


def _scenario_legend(ax: plt.Axes) -> None:
    """Draw outcome-color and scenario-hatch legends."""
    sev = ax.legend(
        handles=[
            Patch(
                facecolor=CRIT_COLOR,
                edgecolor=EDGE,
                linewidth=0.35,
                label="Critical",
            ),
            Patch(
                facecolor=BEN_COLOR,
                edgecolor=EDGE,
                linewidth=0.35,
                label="Benign",
            ),
        ],
        fontsize=FS_LEGEND,
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.0, 0.02),
    )
    ax.add_artist(sev)
    pairs = [
        Patch(
            facecolor=SEA_COLORS["white"],
            hatch=SCENARIO_HATCHES[i],
            edgecolor=EDGE,
            linewidth=0.35,
        )
        for i in range(4)
    ]
    ax.legend(
        handles=pairs,
        labels=SETTINGS,
        handlelength=1.2,
        fontsize=FS_LEGEND,
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.0, 0.17),
        title="scenario (hatch)",
        title_fontsize=FS_LEGEND,
    )


def _draw_panel(
    ax: plt.Axes, agg: dict, role: str, keep: list[str], with_title: bool
) -> None:
    height = 0.24
    offsets = [1.5, 0.5, -0.5, -1.5]
    ypos = list(range(len(keep)))
    for si, setting in enumerate(SETTINGS):
        ys = [y + offsets[si] * height for y in ypos]
        crit = [agg[(setting, role, t, "crit")] for t in keep]
        ben = [agg[(setting, role, t, "benign")] for t in keep]
        alpha = SCENARIO_ALPHA[si]
        ax.barh(
            ys,
            crit,
            height=height,
            color=CRIT_COLOR,
            alpha=alpha,
            edgecolor=EDGE,
            linewidth=0.5,
            hatch=SCENARIO_HATCHES[si],
            zorder=3,
        )
        ax.barh(
            ys,
            ben,
            height=height,
            left=crit,
            color=BEN_COLOR,
            alpha=alpha,
            edgecolor=EDGE,
            linewidth=0.5,
            hatch=SCENARIO_HATCHES[si],
            zorder=3,
        )

    ax.set_yticks(ypos)
    ax.set_yticklabels([TAG_LABEL[t] for t in keep], fontsize=FS_TICK)
    ax.invert_yaxis()
    ax.set_xlabel(f"average error occurrences per 100 {role} turns", fontsize=FS_LABEL)
    if with_title:
        ax.set_title(
            f"{role.capitalize()} errors",
            fontsize=FS_TITLE,
            fontweight="bold",
            loc="left",
        )
    ax.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=FS_TICK)


def build_role_tag_rates_figure(agg: dict) -> plt.Figure:
    """Appendix figure: agent + user, all 13 tags, two panels side by side."""
    with plt.rc_context({"hatch.linewidth": 1.3}):
        fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.3))
        for ax, role in zip(axes, ("agent", "user")):
            keep, _dropped = tags_for(agg, role, threshold=0.0)
            _draw_panel(ax, agg, role, keep, with_title=True)
            if role == "agent":
                _scenario_legend(ax)
        fig.tight_layout(rect=(0, 0.02, 1, 1))
    return fig


def _draw_grouped_panel(
    ax: plt.Axes,
    agg: dict,
    role: str,
    keep: list[str],
    tick_fontsize: float = 7.2,
    label_fontsize: float = 6.4,
    wrap_label: bool = True,
) -> None:
    """Draw scenario-colored bars with severity hatches."""
    height = 0.19
    offsets = [1.5, 0.5, -0.5, -1.5]
    ypos = list(range(len(keep)))
    for si, setting in enumerate(SETTINGS):
        ys = [y + offsets[si] * height for y in ypos]
        crit = [agg[(setting, role, t, "crit")] for t in keep]
        ben = [agg[(setting, role, t, "benign")] for t in keep]
        color = SCENARIO_COLORS[setting]
        ax.barh(
            ys,
            crit,
            height=height,
            color=color,
            alpha=SEVERITY_ALPHA["crit"],
            hatch=SEVERITY_HATCH["crit"],
            edgecolor=EDGE,
            linewidth=0.35,
            zorder=3,
        )
        ax.barh(
            ys,
            ben,
            height=height,
            left=crit,
            color=color,
            alpha=SEVERITY_ALPHA["benign"],
            hatch=SEVERITY_HATCH["benign"],
            edgecolor=EDGE,
            linewidth=0.35,
            zorder=3,
        )
    ax.set_yticks(ypos)
    ax.set_yticklabels([TAG_LABEL[t] for t in keep], fontsize=tick_fontsize)
    ax.invert_yaxis()
    # Wrap the label in the narrow layout.
    label = f"average error occurrences per 100 {role} turns"
    if wrap_label:
        label = f"average error occurrences\nper 100 {role} turns"
    ax.set_xlabel(label, fontsize=label_fontsize)
    ax.grid(axis="x", color="#dddddd", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=tick_fontsize)


def build_agent_tag_rates_figure(
    agg: dict, top_n: int = DEFAULT_TOP_N, wide: bool = False
) -> plt.Figure:
    """Build the agent figure for the top ``top_n`` tags.

    ``wide`` switches to a two-column layout.
    """
    keep = top_tags(agg, "agent", top_n)
    width = PLOT_TWO_COLUMN_WIDTH if wide else PLOT_COLUMN_WIDTH
    height = (0.34 if wide else 0.44) * len(keep) + 1.15
    fig, ax = plt.subplots(figsize=(width, height))
    _draw_grouped_panel(
        ax,
        agg,
        "agent",
        keep,
        tick_fontsize=7.6 if wide else 7.2,
        label_fontsize=7.6 if wide else 6.4,
        wrap_label=not wide,
    )

    scen_handles = [
        Patch(facecolor=SCENARIO_COLORS[s], edgecolor=EDGE, linewidth=0.35, label=s)
        for s in SETTINGS
    ]
    sev_handles = [
        Patch(
            facecolor=SEA_COLORS["black"],
            alpha=SEVERITY_ALPHA["crit"],
            hatch=SEVERITY_HATCH["crit"],
            edgecolor=EDGE,
            linewidth=0.35,
            label="Critical",
        ),
        Patch(
            facecolor=SEA_COLORS["black"],
            alpha=SEVERITY_ALPHA["benign"],
            hatch=SEVERITY_HATCH["benign"],
            edgecolor=EDGE,
            linewidth=0.35,
            label="Benign",
        ),
    ]
    sev_legend = ax.legend(
        handles=sev_handles,
        fontsize=6.6,
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.0, 0.01),
        handlelength=1.2,
        labelspacing=0.3,
    )
    ax.add_artist(sev_legend)
    ax.legend(
        handles=scen_handles,
        fontsize=6.6,
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(1.0, 0.16),
        title="scenario",
        title_fontsize=6.6,
        handlelength=1.2,
        labelspacing=0.3,
    )
    # Explicit margins preserve the long x-axis label.
    fig.subplots_adjust(
        top=0.98,
        bottom=0.10 if wide else 0.085,
        left=0.20 if wide else 0.39,
        right=0.98,
    )
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ERROR_TAG_RATES_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help="Number of leading agent error tags to show in the main-text "
        "figure (remaining tags are covered in the appendix figure).",
    )
    parser.add_argument(
        "--wide",
        action="store_true",
        help="Render the main-text figure at two-column width instead of "
        "a tall single column.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    df = load_data(args.csv)
    if df.empty:
        raise SystemExit(f"No error-tag rows found in {args.csv}")
    agg = aggregate(df)

    formats = tuple(args.formats)
    for output in save_figure(
        build_role_tag_rates_figure(agg), ROLE_TAG_RATES_STEM, args.output_dir, formats
    ):
        print(output)
    for output in save_figure(
        build_agent_tag_rates_figure(agg, top_n=args.top_n, wide=args.wide),
        AGENT_TAG_RATES_STEM,
        args.output_dir,
        formats,
    ):
        print(output)


if __name__ == "__main__":
    main()
