"""Regenerate ``data/analyses/error_tag_rates.csv`` from the LLM-judge
per-cell error-tag counts exported by the review pipeline.

The upstream export (``error_tag_rates_raw.csv``) has one row per
(setting, language, domain) cell: three plain sim-outcome counts per role
(``<role>_critical_error`` / ``<role>_minor_error`` / ``<role>_correct``),
plus one column per (role, tag) pair that packs both severities into a
single string, e.g. ``"crit:4 / min:8"``. That packed string is awkward to
consume from a CSV -- every reader has to re-parse it -- so this script
unpacks it once into a tidy long table: one row per
(setting, language, domain, role, category, severity), with a plain integer
``count``.

Rates in this dataset are "per 100 turns" (matching the paper and the
figure this feeds), not "per 100 simulations". The raw export itself has no
turn counts -- and the per-simulation ``results_reviewed.json`` files the
old JSON-walking version of this pipeline used to get them from are no
longer present under ``data/simulations/`` (only the unreviewed
``results.json`` remains there now; the review step's output format
changed to this CSV export). So turn counts are pulled from
``experiment_language_summary.csv`` instead: it has ``agent_turns_total``/
``user_turns_total`` per experiment run (one row per
scenario x domain x language x model).

The LLM-judge review this dataset comes from only ever covers the
gpt-5-mini agent (judged by DeepSeek-V4-Flash) -- confirmed directly, not
inferred -- so turn totals are taken from gpt-5-mini's row only, not summed
across the 3 agent models each cell's experiment_language_summary.csv rows
cover. An earlier version of this script summed turns across all 3 models,
which overcounted by roughly 3x: every model happens to run the exact same
number of simulations per (domain, language) cell (50 or 114 tasks x 3
trials), so error_tag_rates_raw.csv's per-cell simulation totals (which
match a single model's count exactly) look deceptively like they could be
either a single model or a coincidentally-equal pooled total -- they are
the former.

Usage:
    uv run python -m seatau.analysis.error_tag_rates
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from paths import (
    ERROR_TAG_RATES_CSV,
    ERROR_TAG_RATES_RAW_CSV,
    EXPERIMENT_LANGUAGE_SUMMARY_CSV,
)

# Column suffixes (and CSV `category` values) for the 13 error tags, in the
# same spelling as the raw export's `agent_<tag>` / `user_<tag>` columns.
# seatau.plot.error_tag_rates imports this list (and TAG_LABEL) so the tag
# set has one source of truth between the data-prep and plotting steps.
TAGS = [
    "guideline_violation",
    "missed_required_action",
    "incorrect_interpretation",
    "premature_termination",
    "inconsistent_behavior",
    "hallucination",
    "wrong_sequence",
    "tool_call_argument_error",
    "irrelevant_tool_call",
    "tool_call_schema_error",
    "revealed_info_early",
    "other",
    "interruption_error",
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

ROLES = ("agent", "user")

# setting (error_tag_rates_raw.csv) -> scenario (experiment_language_summary.csv)
SCENARIO_BY_SETTING = {
    "English Baseline": "english",
    "L2 Interaction": "l2_interaction",
    "L2 Tool": "l2_tools",
    "L2 Domain": "l2_domain",
}

# The only agent model the LLM-judge error review covers (confirmed, not
# inferred) -- see the module docstring. experiment_language_summary.csv
# has rows for gpt-5-mini, qwen-3-235b-it, and kimi-k2.5 per cell; only
# this one matches what was actually reviewed.
REVIEWED_AGENT_MODEL = "gpt-5-mini"

_PACKED_RE = re.compile(r"crit:\s*(\d+)\s*/\s*min:\s*(\d+)")


def _parse_packed(value: object) -> tuple[int, int]:
    """Split a raw ``"crit:<n> / min:<n>"`` cell into (critical, benign)."""
    if pd.isna(value):
        return 0, 0
    match = _PACKED_RE.match(str(value).strip())
    if not match:
        raise ValueError(f"Unrecognized packed error-count cell: {value!r}")
    return int(match.group(1)), int(match.group(2))


def _load_turn_totals(summary_csv: Path) -> pd.DataFrame:
    """Turn totals per (scenario, domain, language) cell for
    REVIEWED_AGENT_MODEL only -- one row per cell already, since
    experiment_language_summary.csv has exactly one row per
    (scenario, domain, language_scenario, model). The groupby-sum just
    guards against an unexpected duplicate row rather than pooling
    multiple models together.
    """
    summary = pd.read_csv(summary_csv)
    summary = summary.loc[summary["normalized_agent_llm"] == REVIEWED_AGENT_MODEL]
    return summary.groupby(["scenario", "domain", "language_scenario"], as_index=False)[
        ["agent_turns_total", "user_turns_total"]
    ].sum()


def build_error_tag_rates(
    raw_csv: Path, summary_csv: Path = EXPERIMENT_LANGUAGE_SUMMARY_CSV
) -> pd.DataFrame:
    """Unpack the raw per-cell export into a tidy long table.

    One row per (setting, language, domain, role, category, severity).
    `category` is "outcome" (severity in critical/benign/correct, from the
    per-simulation classification columns) or one of TAGS (severity in
    critical/benign, from the packed tag columns).

    Each row carries two denominators: `turns` is the role's turn count for
    REVIEWED_AGENT_MODEL in that (setting, language, domain) cell, from
    `experiment_language_summary.csv` -- the rate denominator for tag rows
    (average error occurrences per 100 turns, matching the paper). `total_sims`
    is the role's simulation count for that cell (critical + benign + correct
    outcomes) -- the natural denominator for "outcome" rows instead, since
    those are a per-simulation classification, not a per-turn count.

    L2 Tool rows whose `language` lists more than one language (the
    Mix-2..5 tool-mix variants) are dropped: those are a separate construct
    from the 5 single-language L2 Tool variants this dataset otherwise
    tracks, matching how the old JSON-based pipeline only ever read the
    single-language folders for L2 Tool. `experiment_language_summary.csv`
    doesn't carry turn totals for the Mix-2..5 variants under these
    `language_scenario` labels either, so dropping them first keeps every
    remaining cell's turn-count merge exact (no unmatched rows).
    """
    raw = pd.read_csv(raw_csv)
    raw["domain"] = raw["domain"].str.lower()
    is_mixed_l2_tool = raw["setting"].eq("L2 Tool") & raw["language"].str.contains(",")
    raw = raw.loc[~is_mixed_l2_tool].reset_index(drop=True)

    turn_totals = _load_turn_totals(summary_csv)
    raw["scenario"] = raw["setting"].map(SCENARIO_BY_SETTING)
    raw["language_scenario"] = raw["language"].str.lower()
    raw = raw.merge(
        turn_totals,
        on=["scenario", "domain", "language_scenario"],
        how="left",
    )
    missing = raw.loc[
        raw["agent_turns_total"].isna(), ["setting", "language", "domain"]
    ]
    if not missing.empty:
        raise ValueError(
            "No turn totals found in "
            f"{summary_csv} for cells:\n{missing.to_string(index=False)}"
        )

    rows: list[dict[str, object]] = []
    for record in raw.to_dict(orient="records"):
        for role in ROLES:
            total_sims = (
                int(record[f"{role}_critical_error"])
                + int(record[f"{role}_minor_error"])
                + int(record[f"{role}_correct"])
            )
            turns = int(record[f"{role}_turns_total"])
            base = {
                "setting": record["setting"],
                "language": record["language"],
                "domain": record["domain"],
                "role": role,
                "turns": turns,
                "total_sims": total_sims,
            }
            rows.append(
                {
                    **base,
                    "category": "outcome",
                    "severity": "critical",
                    "count": int(record[f"{role}_critical_error"]),
                }
            )
            rows.append(
                {
                    **base,
                    "category": "outcome",
                    "severity": "benign",
                    "count": int(record[f"{role}_minor_error"]),
                }
            )
            rows.append(
                {
                    **base,
                    "category": "outcome",
                    "severity": "correct",
                    "count": int(record[f"{role}_correct"]),
                }
            )
            for tag in TAGS:
                crit, benign = _parse_packed(record[f"{role}_{tag}"])
                rows.append(
                    {**base, "category": tag, "severity": "critical", "count": crit}
                )
                rows.append(
                    {**base, "category": tag, "severity": "benign", "count": benign}
                )

    columns = [
        "setting",
        "language",
        "domain",
        "role",
        "category",
        "severity",
        "count",
        "turns",
        "total_sims",
    ]
    return pd.DataFrame(rows, columns=columns)


def write_error_tag_rates(
    raw_csv: Path = ERROR_TAG_RATES_RAW_CSV,
    output: Path = ERROR_TAG_RATES_CSV,
    *,
    summary_csv: Path = EXPERIMENT_LANGUAGE_SUMMARY_CSV,
) -> Path:
    """Write the regenerated tidy error-tag dataset and return its path."""
    output.parent.mkdir(parents=True, exist_ok=True)
    build_error_tag_rates(raw_csv, summary_csv).to_csv(output, index=False)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-csv", type=Path, default=ERROR_TAG_RATES_RAW_CSV)
    parser.add_argument(
        "--summary-csv", type=Path, default=EXPERIMENT_LANGUAGE_SUMMARY_CSV
    )
    parser.add_argument("--output", type=Path, default=ERROR_TAG_RATES_CSV)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        write_error_tag_rates(args.raw_csv, args.output, summary_csv=args.summary_csv)
    )


if __name__ == "__main__":
    main()
