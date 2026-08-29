"""Per-tag error rates from LLM-judge reviews, across the four scenarios.

Aggregation chain (all values are average error occurrences per 100 turns of
the relevant role -- agent errors per assistant turn, user errors per user
turn):
  1. per simulation, count error instances matching (role, tag, severity)
  2. pool within each cell (scenario x language x domain):
       sum(instances) / sum(role-matched turns) x 100
  3. unweighted mean over the 3 domains
  4. unweighted mean over the 5 L2 languages
     (English Baseline has no language axis; L2 Tool uses the 5
     single-language variants only -- Mix-2..5 are a separate construct)

A turn may be flagged more than once with the same tag, possibly at
different severities, so these are rates rather than a percentage of turns.

Reads results_reviewed.json directly rather than a precomputed
data/analyses/*.csv, unlike most modules in this package -- there is no
upstream analysis step producing per-tag rates yet.

Produces two figures from one aggregation:
  avg_error_tags_occ_per_100_turns  agent + user, all 13 tags (two panels)
  avg_error_tags_occ_agent          agent only, single column, for the main
                                     text (drops tags below PLOT_THRESHOLD)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
from matplotlib.patches import Patch

from paths import PROJECT_DATA_DIR
from seatau.plot.config import DEFAULT_FIG_DIR, EXPORT_FORMATS, SEA_COLORS
from seatau.plot.plot_utils import apply_style, save_figure

ROLE_TAG_RATES_STEM = "avg_error_tags_occ_per_100_turns"
AGENT_TAG_RATES_STEM = "avg_error_tags_occ_agent"

TAGS = [
    "guideline_violation", "missed_required_action", "incorrect_interpretation",
    "premature_termination", "inconsistent_behavior", "hallucination", "wrong_sequence",
    "tool_call_argument_error", "irrelevant_tool_call", "tool_call_schema_error",
    "revealed_info_early", "other", "interruption_error",
]

TAG_LABEL = {
    "guideline_violation": "Guideline Violation",
    "missed_required_action": "Missed Required Action",
    "incorrect_interpretation": "Incorrect Interpretation",
    "premature_termination": "Premature Termination",
    "inconsistent_behavior": "Inconsistent Behavior",
    "hallucination": "Hallucination",
    "wrong_sequence": "Wrong Sequence",
    "tool_call_argument_error": "Tool Call Argument Error",
    "irrelevant_tool_call": "Irrelevant Tool Call",
    "tool_call_schema_error": "Tool Call Schema Error",
    "revealed_info_early": "Revealed Info Early",
    "other": "Other",
    "interruption_error": "Interruption Error",
}

SETTINGS = ["English Baseline", "L2 Interaction", "L2 Tool", "L2 Domain"]
DOMAINS = ["airline", "retail", "telecom"]

DATA_DIRS = [
    ("English Baseline", "english-baseline-simulations"),
    ("L2 Interaction", "crosslingual-simulations"),
    ("L2 Tool", "tool-adaptation-simulations"),
    ("L2 Domain", "l2-domain-simulations"),
]

LANG = {
    "vietnamese": "VI", "thai": "TH", "indonesian": "ID", "chinese": "ZH", "filipino": "FIL",
    "vi": "VI", "th": "TH", "id": "ID", "zh": "ZH", "tl": "FIL",
}
SINGLE_TOOL = {"vi_tools": "VI", "th_tools": "TH", "id_tools": "ID",
               "zh_tools": "ZH", "tl_tools": "FIL"}

# Tags below this many instances per simulation (max over scenarios) are
# dropped from the agent-only main-text figure. The all-tags appendix figure
# ignores this -- the point there is to show the rare ones are rare, not to
# hide them.
PLOT_THRESHOLD = 0.01

# Type sizes are printed sizes, not rcParam defaults: these panels are far
# denser (13 rows x 4 scenarios) than what config.py's PLOT_* sizes assume,
# so every text call below passes fontsize= explicitly rather than relying
# on apply_style()'s rcParams.
FS_TICK, FS_LABEL, FS_TITLE, FS_LEGEND = 6.0, 6.5, 8.0, 6.0

# Same assignment as error_breakdown.py (critical = blue, benign = red), but
# that figure uses a flat alpha=0.5; here alpha additionally encodes the
# scenario, so English Baseline renders at exactly error_breakdown.py's shade
# and L2 Domain renders at the raw config hex.
CRIT_COLOR = SEA_COLORS["blue"]
BEN_COLOR = SEA_COLORS["red"]
EDGE = SEA_COLORS["black"]
SCENARIO_ALPHA = [0.5, 0.67, 0.83, 1.0]


def parse_meta(setting: str, folder: str) -> tuple[str | None, str | None]:
    """Return (language_or_variant, domain) or (None, None)."""
    if setting == "English Baseline":
        return "EN", next((d for d in DOMAINS if f"_{d}_llm_agent" in folder), None)
    if setting == "L2 Interaction":
        dom = next((d for d in DOMAINS if f"_{d}_llm_agent" in folder), None)
        return LANG.get(folder.split("crosslingual_")[-1]), dom
    if setting == "L2 Domain":
        parts = folder.split("_")
        if parts[1] == "translated":
            return LANG.get(parts[4]), parts[2]
        return LANG.get(parts[2]), parts[1]
    # L2 Tool: single-language variants only (Mix-2..5 are a separate construct)
    dom = next((d for d in DOMAINS if f"_tool_experiments_{d}_" in folder), None)
    suffix = next((s for s in SINGLE_TOOL if folder.endswith(f"_{s}")), None)
    return SINGLE_TOOL.get(suffix), dom


def collect_cells(data_dir: Path) -> dict:
    """Walk results_reviewed.json under data_dir, one cell per
    (scenario, language, domain), counting error occurrences and turns."""
    cells: dict = defaultdict(
        lambda: {"sims": 0, "agent_turns": 0, "user_turns": 0, "counts": Counter()}
    )
    for setting, sub in DATA_DIRS:
        root = data_dir / sub
        if not root.is_dir():
            continue
        for folder in sorted(p.name for p in root.iterdir()):
            path = root / folder / "results_reviewed.json"
            if not path.is_file():
                continue
            lang, domain = parse_meta(setting, folder)
            if not lang or domain not in DOMAINS:
                continue
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            cell = cells[(setting, lang, domain)]
            for sim in data.get("simulations", []):
                cell["sims"] += 1
                roles = Counter(m.get("role") for m in sim.get("messages", []))
                cell["agent_turns"] += roles["assistant"]
                cell["user_turns"] += roles["user"]
                for err in (sim.get("review") or {}).get("errors", []):
                    role = err.get("source")
                    if role not in ("agent", "user"):
                        continue
                    sev = err.get("severity")
                    bucket = (
                        "crit"
                        if sev in ("critical", "critical_helped", "critical_hindered")
                        else "benign"
                    )
                    for tag in set(err.get("error_tags") or []):
                        if tag in TAGS:
                            cell["counts"][(role, tag, bucket)] += 1
    return cells


def cell_rate(cell: dict, role: str, tag: str, bucket: str) -> float:
    """Average error occurrences per 100 turns of `role` in this cell."""
    num = cell["counts"][(role, tag, bucket)]
    den = cell["agent_turns"] if role == "agent" else cell["user_turns"]
    return 100.0 * num / den if den else 0.0


def aggregate(cells: dict) -> dict:
    """Unweighted mean over domains, then over languages, per (scenario,
    role, tag, severity)."""
    out = {}
    for setting in SETTINGS:
        langs = sorted({lang for (s, lang, _d) in cells if s == setting})
        for role in ("agent", "user"):
            for tag in TAGS:
                for bucket in ("crit", "benign"):
                    per_lang = []
                    for lang in langs:
                        per_dom = [
                            cell_rate(cells[(setting, lang, d)], role, tag, bucket)
                            for d in DOMAINS
                            if (setting, lang, d) in cells
                        ]
                        if per_dom:
                            per_lang.append(sum(per_dom) / len(per_dom))
                    out[(setting, role, tag, bucket)] = (
                        sum(per_lang) / len(per_lang) if per_lang else 0.0
                    )
    return out


def tags_for(agg: dict, role: str, threshold: float) -> tuple[list[str], list[str]]:
    """Tags reaching `threshold` in at least one scenario for `role`,
    ranked by L2 Domain total, descending."""
    keep = [
        t for t in TAGS
        if max(agg[(s, role, t, "crit")] + agg[(s, role, t, "benign")] for s in SETTINGS)
        >= threshold
    ]
    keep.sort(
        key=lambda t: -(agg[("L2 Domain", role, t, "crit")] + agg[("L2 Domain", role, t, "benign")])
    )
    dropped = [t for t in TAGS if t not in keep]
    return keep, dropped


def _scenario_legend(ax: plt.Axes) -> None:
    """Severity legend (full-strength swatches) plus a paired scenario-shade
    legend, both drawn once on the axes with the most room."""
    sev = ax.legend(
        handles=[
            Patch(facecolor=CRIT_COLOR, edgecolor=EDGE, linewidth=0.35, label="Critical"),
            Patch(facecolor=BEN_COLOR, edgecolor=EDGE, linewidth=0.35, label="Benign"),
        ],
        fontsize=FS_LEGEND, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.02),
    )
    ax.add_artist(sev)
    pairs = [
        (
            Patch(facecolor=CRIT_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE, linewidth=0.35),
            Patch(facecolor=BEN_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE, linewidth=0.35),
        )
        for i in range(4)
    ]
    ax.legend(
        handles=pairs, labels=SETTINGS,
        handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)},
        handlelength=2.0, fontsize=FS_LEGEND, frameon=False,
        loc="lower right", bbox_to_anchor=(1.0, 0.17),
        title="scenario (shade)", title_fontsize=FS_LEGEND,
    )


def _draw_panel(ax: plt.Axes, agg: dict, role: str, keep: list[str], with_title: bool) -> None:
    height = 0.20
    offsets = [1.5, 0.5, -0.5, -1.5]
    ypos = list(range(len(keep)))
    for si, setting in enumerate(SETTINGS):
        ys = [y + offsets[si] * height for y in ypos]
        crit = [agg[(setting, role, t, "crit")] for t in keep]
        ben = [agg[(setting, role, t, "benign")] for t in keep]
        alpha = SCENARIO_ALPHA[si]
        ax.barh(ys, crit, height=height, color=CRIT_COLOR, alpha=alpha,
                edgecolor=EDGE, linewidth=0.35, zorder=3)
        ax.barh(ys, ben, height=height, left=crit, color=BEN_COLOR, alpha=alpha,
                edgecolor=EDGE, linewidth=0.35, zorder=3)

    ax.set_yticks(ypos)
    ax.set_yticklabels([TAG_LABEL[t] for t in keep], fontsize=FS_TICK)
    ax.invert_yaxis()
    ax.set_xlabel(f"average error occurrences per 100 {role} turns", fontsize=FS_LABEL)
    if with_title:
        ax.set_title(f"{role.capitalize()} errors", fontsize=FS_TITLE,
                     fontweight="bold", loc="left")
    ax.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=FS_TICK)


def build_role_tag_rates_figure(agg: dict) -> plt.Figure:
    """Appendix figure: agent + user, all 13 tags, two panels side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.35))
    for ax, role in zip(axes, ("agent", "user")):
        keep, _dropped = tags_for(agg, role, threshold=0.0)
        _draw_panel(ax, agg, role, keep, with_title=True)
        if role == "agent":
            _scenario_legend(ax)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    return fig


def build_agent_tag_rates_figure(agg: dict) -> plt.Figure:
    """Main-text figure: agent only, single column, tags below
    PLOT_THRESHOLD dropped."""
    keep, dropped = tags_for(agg, "agent", threshold=PLOT_THRESHOLD)
    if dropped:
        print(f"  agent panel omitted (<{PLOT_THRESHOLD:g} per simulation in "
              f"every scenario): {', '.join(dropped)}")
    fig, ax = plt.subplots(figsize=(3.35, 3.2))
    _draw_panel(ax, agg, "agent", keep, with_title=False)
    ax.tick_params(axis="both", labelsize=5.8)
    ax.set_yticklabels([TAG_LABEL[t] for t in keep], fontsize=5.8)
    ax.set_xlabel("average error occurrences per 100 agent turns", fontsize=6.2)
    sev = ax.legend(
        handles=[
            Patch(facecolor=CRIT_COLOR, edgecolor=EDGE, linewidth=0.3, label="Critical"),
            Patch(facecolor=BEN_COLOR, edgecolor=EDGE, linewidth=0.3, label="Benign"),
        ],
        fontsize=5.8, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.01),
        handlelength=1.3, labelspacing=0.3,
    )
    ax.add_artist(sev)
    pairs = [
        (
            Patch(facecolor=CRIT_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE, linewidth=0.3),
            Patch(facecolor=BEN_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE, linewidth=0.3),
        )
        for i in range(4)
    ]
    ax.legend(
        handles=pairs, labels=SETTINGS,
        handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)},
        handlelength=1.8, fontsize=5.8, frameon=False, loc="lower right",
        bbox_to_anchor=(1.0, 0.16), title="scenario (shade)", title_fontsize=5.8,
        labelspacing=0.3,
    )
    fig.tight_layout()
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--formats", nargs="+", default=list(EXPORT_FORMATS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    apply_style()
    cells = collect_cells(args.data_dir)
    if not cells:
        raise SystemExit(f"No results_reviewed.json found under {args.data_dir}")
    agg = aggregate(cells)

    formats = tuple(args.formats)
    for output in save_figure(build_role_tag_rates_figure(agg), ROLE_TAG_RATES_STEM,
                              args.output_dir, formats):
        print(output)
    for output in save_figure(build_agent_tag_rates_figure(agg), AGENT_TAG_RATES_STEM,
                              args.output_dir, formats):
        print(output)


if __name__ == "__main__":
    main()
