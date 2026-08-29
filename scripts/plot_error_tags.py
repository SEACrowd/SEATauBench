"""Summarise the 6 error-tag tables into one figure per denominator variant.

Aggregation chain (identical for both variants, only the denominator differs):
  1. per simulation, count error instances matching (role, tag, severity)
  2. pool within each cell (setting x language x domain):
       per_sim  : sum(instances) / n_simulations
       per_turn : sum(instances) / sum(role-matched turns)      [pooled, not mean-of-ratios]
  3. unweighted mean over the 3 domains
  4. unweighted mean over the 5 languages
     (English Only has no language axis; L2 Tool uses the 5 single-language variants only)

Outputs (scripts/figures/):
  error_tags_per_sim.pdf/.png    error instances per simulation
  error_tags_per_turn.pdf/.png   error instances per role-matched turn
  error_tags_aggregated.csv      the numbers behind both figures

Run with the system Python (matplotlib is not in .venv):
    python scripts/plot_error_tags.py
"""

import csv
import json
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.legend_handler import HandlerTuple

# ── configuration ─────────────────────────────────────────────────────────────

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "scripts", "figures")

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

# Reviewer-facing families. An error instance joins a family if ANY of its tags
# belong to it, so no double counting inside a family; an instance CAN join two
# families (23.5% do), so family values do not sum to the error total.
FAMILIES = {
    "Policy & procedure": {"guideline_violation", "missed_required_action",
                           "wrong_sequence", "premature_termination"},
    "Tool-schema logic": {"tool_call_schema_error", "tool_call_argument_error",
                          "irrelevant_tool_call"},
    "Comprehension": {"incorrect_interpretation", "hallucination",
                      "inconsistent_behavior"},
    "Other": {"revealed_info_early", "other", "interruption_error"},
}
FAM_KEYS = ["FAM::" + f for f in FAMILIES]

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

# only tags reaching this many instances per simulation (max over settings) are plotted
PLOT_THRESHOLD = 0.01  # keeps both tool-call tags visible for the agent panel
# In-figure type sizes. Native width ~= ACL 	extwidth, so these are the PRINTED
# point sizes. Lower them for more bar area, raise them for legibility.
FS_TICK, FS_LABEL, FS_TITLE, FS_LEGEND = 6.0, 6.5, 8.0, 6.0

# Palette from src/seatau/plot/config.py, applied the same way as Figure 5
# (src/seatau/plot/error_breakdown.py): critical = blue, benign = red, black edges.
# Figure 5 uses a single alpha of 0.5; here alpha additionally encodes the scenario.
SEA_COLORS = {
    "red": "#ed2939",
    "blue": "#0042a6",
    "yellow": "#f9e300",
    "white": "#ffffff",
    "black": "#111111",
}
CRIT_COLOR = SEA_COLORS["blue"]
BEN_COLOR = SEA_COLORS["red"]
EDGE = SEA_COLORS["black"]
SCENARIO_ALPHA = [0.5, 0.67, 0.83, 1.0]  # English Baseline -> L2 Domain.
# 0.5 is exactly the flat alpha Figure 5 uses, 1.0 is the raw config hex, so every
# bar sits between the two figures' existing shades.

plt.rcParams.update({
    "savefig.dpi": 400,
    "savefig.bbox": "tight",
    "savefig.facecolor": SEA_COLORS["white"],
    "font.family": ("Helvetica Neue", "Avenir Next", "DejaVu Sans"),
    "font.size": 8,
    "figure.facecolor": SEA_COLORS["white"],
    "axes.facecolor": SEA_COLORS["white"],
    "text.color": SEA_COLORS["black"],
    "axes.labelcolor": SEA_COLORS["black"],
    "axes.edgecolor": SEA_COLORS["black"],
    "xtick.color": SEA_COLORS["black"],
    "ytick.color": SEA_COLORS["black"],
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.titleweight": "bold",
    "axes.labelweight": "bold",
    "axes.linewidth": 0.7,
    "grid.linewidth": 0.45,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def parse_meta(setting, folder):
    """Return (language_or_variant, domain) or (None, None)."""
    if setting == "English Baseline":
        return "EN", next((d for d in DOMAINS if "_%s_llm_agent" % d in folder), None)
    if setting == "L2 Interaction":
        dom = next((d for d in DOMAINS if "_%s_llm_agent" % d in folder), None)
        return LANG.get(folder.split("crosslingual_")[-1]), dom
    if setting == "L2 Domain":
        parts = folder.split("_")
        if parts[1] == "translated":
            return LANG.get(parts[4]), parts[2]
        return LANG.get(parts[2]), parts[1]
    # L2 Tool: single-language variants only (Mix-2..5 are a separate construct)
    dom = next((d for d in DOMAINS if "_tool_experiments_%s_" % d in folder), None)
    suffix = next((s for s in SINGLE_TOOL if folder.endswith("_" + s)), None)
    return (SINGLE_TOOL.get(suffix), dom)


# ── step 1-2: collect per cell ────────────────────────────────────────────────

cells = defaultdict(lambda: {"sims": 0, "agent_turns": 0, "user_turns": 0,
                             "counts": Counter()})

for setting, sub in DATA_DIRS:
    root = os.path.join(ROOT, "data", sub)
    for folder in sorted(os.listdir(root)):
        path = os.path.join(root, folder, "results_reviewed.json")
        if not os.path.isfile(path):
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
                bucket = "crit" if sev in ("critical", "critical_helped",
                                           "critical_hindered") else "benign"
                etags = set(err.get("error_tags") or [])
                for tag in etags:
                    if tag in TAGS:
                        cell["counts"][(role, tag, bucket)] += 1
                for fam, members in FAMILIES.items():
                    if etags & members:
                        cell["counts"][(role, "FAM::" + fam, bucket)] += 1

print("cells: %d" % len(cells))


def cell_rate(cell, role, tag, bucket, variant):
    num = cell["counts"][(role, tag, bucket)]
    if variant == "per_sim":
        den = cell["sims"]
        return num / den if den else 0.0
    den = cell["agent_turns"] if role == "agent" else cell["user_turns"]
    # scaled x100: "instances per 100 turns" reads far better than 0.0628
    return 100.0 * num / den if den else 0.0


# ── step 3-4: domains then languages, both unweighted ─────────────────────────

def aggregate(variant):
    out = {}
    for setting in SETTINGS:
        langs = sorted({l for (s, l, d) in cells if s == setting})
        for role in ("agent", "user"):
            for tag in TAGS + FAM_KEYS:
                for bucket in ("crit", "benign"):
                    per_lang = []
                    for lang in langs:
                        per_dom = [cell_rate(cells[(setting, lang, d)], role, tag,
                                             bucket, variant)
                                   for d in DOMAINS if (setting, lang, d) in cells]
                        if per_dom:
                            per_lang.append(sum(per_dom) / len(per_dom))
                    out[(setting, role, tag, bucket)] = (
                        sum(per_lang) / len(per_lang) if per_lang else 0.0)
    return out


AGG = {v: aggregate(v) for v in ("per_sim", "per_turn")}

# mean role-matched turns per simulation, per setting (for the caption/checks)
turns_per_sim = {}
for setting in SETTINGS:
    ks = [k for k in cells if k[0] == setting]
    sims = sum(cells[k]["sims"] for k in ks)
    turns_per_sim[setting] = (sum(cells[k]["agent_turns"] for k in ks) / sims,
                              sum(cells[k]["user_turns"] for k in ks) / sims)

print("\nmean turns per simulation (agent / user):")
for s in SETTINGS:
    print("  %-16s %.2f / %.2f" % (s, turns_per_sim[s][0], turns_per_sim[s][1]))


# ── csv ───────────────────────────────────────────────────────────────────────

os.makedirs(OUT, exist_ok=True)
csv_path = os.path.join(OUT, "error_tags_aggregated.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["variant", "setting", "role", "tag", "critical", "benign", "total"])
    for variant in ("per_sim", "per_turn"):
        for setting in SETTINGS:
            for role in ("agent", "user"):
                for tag in TAGS + FAM_KEYS:
                    c = AGG[variant][(setting, role, tag, "crit")]
                    b = AGG[variant][(setting, role, tag, "benign")]
                    w.writerow([variant, setting, role, tag,
                                "%.6f" % c, "%.6f" % b, "%.6f" % (c + b)])
print("\nwrote %s" % csv_path)


# ── plotting ──────────────────────────────────────────────────────────────────

def tags_for(role, threshold=PLOT_THRESHOLD):
    """Tags worth plotting, ranked by L2 Domain total (per-simulation scale)."""
    keep = [t for t in TAGS
            if max(AGG["per_sim"][(s, role, t, "crit")] + AGG["per_sim"][(s, role, t, "benign")]
                   for s in SETTINGS) >= threshold]
    keep.sort(key=lambda t: -(AGG["per_sim"][("L2 Domain", role, t, "crit")]
                              + AGG["per_sim"][("L2 Domain", role, t, "benign")]))
    dropped = [t for t in TAGS if t not in keep]
    return keep, dropped


AXIS_LABEL = {
    "per_sim": "average error occurrences per simulation",
    "per_turn": "average error occurrences per 100 %s turns",
}


def make_figure(variant):
    # Panels side by side, authored at roughly the printed size (ACL \textwidth is
    # ~6.3in) so \includegraphics barely rescales and the labels stay legible.
    keeps = {r: tags_for(r, 0.0) for r in ("agent", "user")}  # appendix: all 13
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.35))  # 2.1:1, matches the wide layout
    height = 0.20
    offsets = [1.5, 0.5, -0.5, -1.5]  # S1 at top of each group

    for ax, role in zip(axes, ("agent", "user")):
        keep, dropped = keeps[role]
        ypos = list(range(len(keep)))
        for si, setting in enumerate(SETTINGS):
            ys = [y + offsets[si] * height for y in ypos]
            crit = [AGG[variant][(setting, role, t, "crit")] for t in keep]
            ben = [AGG[variant][(setting, role, t, "benign")] for t in keep]
            alpha = SCENARIO_ALPHA[si]
            ax.barh(ys, crit, height=height, color=CRIT_COLOR, alpha=alpha,
                    edgecolor=EDGE, linewidth=0.35, zorder=3)
            ax.barh(ys, ben, height=height, left=crit, color=BEN_COLOR, alpha=alpha,
                    edgecolor=EDGE, linewidth=0.35, zorder=3)

        ax.set_yticks(ypos)
        ax.set_yticklabels([TAG_LABEL[t] for t in keep], fontsize=FS_TICK)
        ax.invert_yaxis()
        ax.set_xlabel(AXIS_LABEL[variant] % role if variant == "per_turn"
                      else AXIS_LABEL[variant], fontsize=FS_LABEL)
        ax.set_title("%s errors" % role.capitalize(), fontsize=FS_TITLE,
                     fontweight="bold", loc="left")
        ax.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="both", length=0, labelsize=FS_TICK)
        # Omitted tags are documented in the caption, not on the figure itself.
        if dropped:
            print("  %-5s omitted (<%.2g per simulation in every scenario): %s"
                  % (role, PLOT_THRESHOLD, ", ".join(dropped)))

        # Both panels share one encoding, so the legends are drawn once, on the
        # taller agent panel, where there is room for them.
        if role != "agent":
            continue
        sev_leg = ax.legend(
            handles=[Patch(facecolor=CRIT_COLOR, edgecolor=EDGE,
                           linewidth=0.35, label="Critical"),
                     Patch(facecolor=BEN_COLOR, edgecolor=EDGE,
                           linewidth=0.35, label="Benign")],
            fontsize=FS_LEGEND, frameon=False, loc="lower right",
            bbox_to_anchor=(1.0, 0.02))
        ax.add_artist(sev_leg)
        pairs = [(Patch(facecolor=CRIT_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE,
                        linewidth=0.35),
                  Patch(facecolor=BEN_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE,
                        linewidth=0.35)) for i in range(4)]
        ax.legend(handles=pairs, labels=SETTINGS,
                  handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)},
                  handlelength=2.0, fontsize=FS_LEGEND, frameon=False,
                  loc="lower right", bbox_to_anchor=(1.0, 0.17),
                  title="scenario (shade)", title_fontsize=FS_LEGEND)

    fig.tight_layout(rect=(0, 0.02, 1, 1))
    for ext in ("pdf", "png"):
        p = os.path.join(OUT, "error_tags_%s.%s" % (variant, ext))
        try:
            fig.savefig(p, dpi=400, bbox_inches="tight")
            print("wrote %s" % p)
        except PermissionError:
            alt = p.replace("." + ext, "_new." + ext)
            fig.savefig(alt, dpi=400, bbox_inches="tight")
            print("LOCKED (close the viewer): %s -> wrote %s instead" % (p, alt))
    plt.close(fig)


def make_family_figure(variant):
    """Main-text summary: four error families, agent and simulated user."""
    fams = sorted(FAMILIES, key=lambda f: -sum(
        AGG[variant][("L2 Domain", "agent", "FAM::" + f, b)] for b in ("crit", "benign")))
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.3))
    height = 0.20
    offsets = [1.5, 0.5, -0.5, -1.5]

    for ax, role in zip(axes, ("agent", "user")):
        ypos = list(range(len(fams)))
        for si, setting in enumerate(SETTINGS):
            a = SCENARIO_ALPHA[si]
            ys = [y + offsets[si] * height for y in ypos]
            crit = [AGG[variant][(setting, role, "FAM::" + f, "crit")] for f in fams]
            ben = [AGG[variant][(setting, role, "FAM::" + f, "benign")] for f in fams]
            ax.barh(ys, crit, height=height, color=CRIT_COLOR, alpha=a,
                    edgecolor=EDGE, linewidth=0.35, zorder=3)
            ax.barh(ys, ben, height=height, left=crit, color=BEN_COLOR, alpha=a,
                    edgecolor=EDGE, linewidth=0.35, zorder=3)
        ax.set_yticks(ypos)
        ax.set_yticklabels(fams, fontsize=FS_TICK)
        ax.invert_yaxis()
        ax.set_xlabel(AXIS_LABEL[variant] % role if variant == "per_turn"
                      else AXIS_LABEL[variant], fontsize=FS_LABEL)
        ax.set_title("%s errors" % role.capitalize(), fontsize=FS_TITLE,
                     fontweight="bold", loc="left")
        ax.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.tick_params(axis="both", length=0, labelsize=FS_TICK)

        if role != "agent":
            continue
        sev = ax.legend(
            handles=[Patch(facecolor=CRIT_COLOR, edgecolor=EDGE,
                           linewidth=0.35, label="Critical"),
                     Patch(facecolor=BEN_COLOR, edgecolor=EDGE,
                           linewidth=0.35, label="Benign")],
            fontsize=FS_LEGEND, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.02))
        ax.add_artist(sev)
        pairs = [(Patch(facecolor=CRIT_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE,
                        linewidth=0.35),
                  Patch(facecolor=BEN_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE,
                        linewidth=0.35)) for i in range(4)]
        ax.legend(handles=pairs, labels=SETTINGS,
                  handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)},
                  handlelength=2.4, fontsize=FS_LEGEND, frameon=False, loc="lower right",
                  bbox_to_anchor=(1.0, 0.22), title="scenario (shade)",
                  title_fontsize=FS_LEGEND)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        q = os.path.join(OUT, "error_families_%s.%s" % (variant, ext))
        try:
            fig.savefig(q, dpi=400, bbox_inches="tight")
            print("wrote %s" % q)
        except PermissionError:
            print("LOCKED: %s" % q)
    plt.close(fig)


def make_agent_column_figure(variant):
    """Single-column, agent only: the main-text figure (PLOT_FIGSIZE_ONE_COL_TALL)."""
    keep, dropped = tags_for("agent", 0.01)  # main text: trim the dead tail
    fig, ax = plt.subplots(figsize=(3.35, 3.2))
    height = 0.20
    offsets = [1.5, 0.5, -0.5, -1.5]
    ypos = list(range(len(keep)))

    for si, setting in enumerate(SETTINGS):
        a = SCENARIO_ALPHA[si]
        ys = [y + offsets[si] * height for y in ypos]
        crit = [AGG[variant][(setting, "agent", t, "crit")] for t in keep]
        ben = [AGG[variant][(setting, "agent", t, "benign")] for t in keep]
        ax.barh(ys, crit, height=height, color=CRIT_COLOR, alpha=a,
                edgecolor=EDGE, linewidth=0.3, zorder=3)
        ax.barh(ys, ben, height=height, left=crit, color=BEN_COLOR, alpha=a,
                edgecolor=EDGE, linewidth=0.3, zorder=3)

    ax.set_yticks(ypos)
    ax.set_yticklabels([TAG_LABEL[t] for t in keep], fontsize=5.8)
    ax.invert_yaxis()
    ax.set_xlabel(AXIS_LABEL[variant] % "agent" if variant == "per_turn"
                  else AXIS_LABEL[variant], fontsize=6.2)
    ax.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=5.8)

    sev = ax.legend(
        handles=[Patch(facecolor=CRIT_COLOR, edgecolor=EDGE,
                       linewidth=0.3, label="Critical"),
                 Patch(facecolor=BEN_COLOR, edgecolor=EDGE,
                       linewidth=0.3, label="Benign")],
        fontsize=5.8, frameon=False, loc="lower right", bbox_to_anchor=(1.0, 0.01),
        handlelength=1.3, labelspacing=0.3)
    ax.add_artist(sev)
    pairs = [(Patch(facecolor=CRIT_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE,
                    linewidth=0.3),
              Patch(facecolor=BEN_COLOR, alpha=SCENARIO_ALPHA[i], edgecolor=EDGE,
                    linewidth=0.3)) for i in range(4)]
    ax.legend(handles=pairs, labels=SETTINGS,
              handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)},
              handlelength=1.8, fontsize=5.8, frameon=False, loc="lower right",
              bbox_to_anchor=(1.0, 0.16), title="scenario (shade)",
              title_fontsize=5.8, labelspacing=0.3)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        q = os.path.join(OUT, "error_tags_agent_col.%s" % ext)
        try:
            fig.savefig(q, dpi=400, bbox_inches="tight")
            print("wrote %s" % q)
        except PermissionError:
            alt = q.replace("." + ext, "_new." + ext)
            fig.savefig(alt, dpi=400, bbox_inches="tight")
            print("LOCKED (close the viewer): %s -> wrote %s instead" % (q, alt))
    plt.close(fig)
    print("  agent-only column figure: %d tags, omitted %s" % (len(keep), dropped))


for variant in ("per_sim", "per_turn"):
    make_figure(variant)
make_family_figure("per_turn")
make_agent_column_figure("per_turn")

# ── console summary: does the denominator change the story? ───────────────────

print("\nsetting totals (all tags, both severities):")
print("%-16s %10s %10s %10s %10s" % ("setting", "agent/sim", "agent/turn",
                                     "user/sim", "user/turn"))
for s in SETTINGS:
    row = []
    for variant in ("per_sim", "per_turn"):
        for role in ("agent", "user"):
            row.append(sum(AGG[variant][(s, role, t, b)]
                           for t in TAGS for b in ("crit", "benign")))
    print("%-16s %10.3f %10.4f %10.3f %10.4f" % (s, row[0], row[2], row[1], row[3]))
