"""Shared helpers for the language degradation figure family."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from paths import ANALYSES_DIR, LANGUAGE_DRIFT_DIAGNOSTICS_DIR
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
    """Replace crosslingual language correctness with refreshed run-level values."""

    run_path = diagnostics_dir / "contextual_run_language.csv"
    if not run_path.exists():
        return df

    run_df = normalize_scenario_column(pd.read_csv(run_path, low_memory=False))
    frame = run_df.loc[
        run_df["scenario"].eq("l2_interaction") & run_df["role"].eq("agent")
    ].copy()
    if frame.empty:
        return df

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
        )["language_correctness"]
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
