"""Shared helpers for the language degradation figure family."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from seatau.constants import ANALYSES_DIR, LANGUAGE_DRIFT_DIAGNOSTICS_DIR
from seatau.plot.config import LANGUAGE_LABELS, SCENARIO_LABELS
from seatau.plot.plot_utils import (
    normalize_scenario_column,
    normalize_scenario_id_series,
)

DEFAULT_ANALYSIS_DIR = ANALYSES_DIR
DEFAULT_TABLE_DIR = ANALYSES_DIR
DEFAULT_LANGUAGE_DIAGNOSTICS_DIR = LANGUAGE_DRIFT_DIAGNOSTICS_DIR

FAILURE_LABELS = {
    "wrong_write_action": "Wrong write action",
    "wrong_write_arguments_or_state": "Wrong write args/state",
    "wrong_read_arguments": "Wrong read args",
    "db_mismatch": "DB mismatch",
    "loop_or_recovery_failure": "Loop/recovery",
    "missing_required_read": "Missing read",
    "premature_final_or_incomplete_resolution": "Premature/incomplete",
}


def _read_analysis_csv(path: Path, name: str) -> pd.DataFrame:
    csv_path = path / name
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing {csv_path}. Run `uv run analyze-all-results --output-dir {path}` first."
        )
    return normalize_scenario_column(pd.read_csv(csv_path, low_memory=False))


def _read_first_existing_analysis_csv(
    path: Path, names: tuple[str, ...]
) -> pd.DataFrame:
    for name in names:
        csv_path = path / name
        if csv_path.exists():
            return normalize_scenario_column(pd.read_csv(csv_path, low_memory=False))
    expected = ", ".join(str(path / name) for name in names)
    raise FileNotFoundError(f"Missing one of: {expected}")


def _scenario_short(series: pd.Series) -> pd.Series:
    normalized = normalize_scenario_id_series(series)
    return normalized.map(SCENARIO_LABELS).fillna(normalized)


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

    turn_df = normalize_scenario_column(pd.read_csv(turn_path, low_memory=False))
    frame = turn_df.loc[
        turn_df["scenario"].eq("l2_interaction")
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
