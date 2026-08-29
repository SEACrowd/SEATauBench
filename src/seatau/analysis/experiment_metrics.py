"""Shared experiment-summary loading and metric aggregation helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from seatau.plot.config import (
    FILTER_SETTING,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    METRIC_RENAMES,
    MODEL_LABELS,
    PRIMARY_METRICS,
    SCENARIO_ID_BY_NAME,
    SCENARIO_LABELS,
)


def normalize_key_series(series: pd.Series) -> pd.Series:
    """Normalize identifier columns used by experiment-summary inputs."""

    return series.astype("string").str.strip().str.lower()


def normalize_scenario_id_series(series: pd.Series) -> pd.Series:
    """Normalize scenario ids to canonical lower-case ids."""

    return normalize_key_series(series)


def parse_scenario_id(series: pd.Series) -> pd.Series:
    """Map canonical scenario names to stable numeric ids."""

    return normalize_scenario_id_series(series).map(SCENARIO_ID_BY_NAME).astype("Int64")


def load_and_prepare(
    csv_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Load, normalize, filter, and deduplicate the experiments CSV."""

    raw = pd.read_csv(csv_path)
    raw.columns = [col.strip() for col in raw.columns]
    df = raw.reset_index(names="source_row").copy()

    for csv_col, metric_key in METRIC_RENAMES.items():
        if csv_col in df.columns:
            df[metric_key] = pd.to_numeric(df[csv_col], errors="coerce")
        else:
            df[metric_key] = np.nan

    df["scenario_raw"] = normalize_scenario_id_series(df["scenario"])
    df["scenario_id"] = parse_scenario_id(df["scenario_raw"])
    df["scenario_label"] = (
        df["scenario_raw"].map(SCENARIO_LABELS).fillna(df["scenario_raw"])
    )

    df["domain_key"] = normalize_key_series(df["domain"])
    df["domain_label"] = df["domain_key"].str.title()
    df["language_key"] = normalize_key_series(df["language_senario"])
    df["language_label"] = (
        df["language_key"].map(LANGUAGE_LABELS).fillna(df["language_key"])
    )
    df["language_display"] = (
        df["language_key"].map(LANGUAGE_DISPLAY_NAMES).fillna(df["language_key"])
    )
    df["language_group"] = np.where(
        df["language_key"].str.startswith("tool_mix_", na=False), "tool_mix", "language"
    )
    df["model_key"] = normalize_key_series(df["normalized_agent_llm"])
    df["model_label"] = df["model_key"].map(MODEL_LABELS).fillna(df["model_key"])

    has_primary_metric = df[list(PRIMARY_METRICS)].notna().any(axis=1)
    filter_mask = (
        df["scenario_raw"].isin(FILTER_SETTING["scenario"])
        & df["domain_key"].isin(FILTER_SETTING["domain"])
        & df["language_key"].isin(FILTER_SETTING["language_senario"])
        & df["model_key"].isin(FILTER_SETTING["normalized_agent_llm"])
    )
    with_metrics = df.loc[filter_mask & has_primary_metric].copy()

    dedupe_keys = ["scenario_raw", "domain_key", "language_key", "model_key"]
    duplicate_summary = (
        with_metrics.groupby(dedupe_keys, dropna=False)
        .size()
        .reset_index(name="row_count")
        .query("row_count > 1")
        .sort_values("row_count", ascending=False)
    )
    clean = (
        with_metrics.sort_values("source_row")
        .drop_duplicates(dedupe_keys, keep="last")
        .sort_values("source_row")
        .reset_index(drop=True)
    )

    audit = {
        "raw_rows": len(raw),
        "rows_matching_filter": int(filter_mask.sum()),
        "filtered_rows_with_primary_metrics_before_dedupe": len(with_metrics),
        "clean_rows_after_dedupe": len(clean),
        "duplicate_groups_resolved": len(duplicate_summary),
        "excluded_rows_by_filter_or_missing_metrics": len(df) - len(with_metrics),
    }
    return raw, df, clean, duplicate_summary, audit


def experiment_language_metric_breakdown(
    clean_df: pd.DataFrame,
    metrics: tuple[str, ...] = PRIMARY_METRICS,
) -> pd.DataFrame:
    """Summarize experiment metrics to domain-model rows with language columns."""

    language_rows = clean_df.loc[clean_df["language_group"].eq("language")].copy()
    long = language_rows.melt(
        id_vars=["domain_label", "model_key", "language_key"],
        value_vars=list(metrics),
        var_name="Metric",
        value_name="value",
    ).dropna(subset=["value"])
    summary = (
        long.groupby(
            ["domain_label", "model_key", "Metric", "language_key"],
            observed=True,
            as_index=False,
        )["value"]
        .mean()
        .pivot_table(
            index=["domain_label", "model_key", "Metric"],
            columns="language_key",
            values="value",
            aggfunc="mean",
        )
        .reindex(columns=LANGUAGE_ORDER)
        .reset_index()
        .rename(columns={"domain_label": "Domain", "model_key": "Model"})
    )
    return summary


def clean_language_metric_rows(experiments_csv: Path) -> pd.DataFrame:
    """Return long-form metric rows for natural-language experiment settings."""

    _, _, clean_df, _, _ = load_and_prepare(experiments_csv)
    language_rows = clean_df.loc[clean_df["language_group"].eq("language")].copy()
    id_vars = [
        "scenario_raw",
        "domain_key",
        "domain_label",
        "model_key",
        "language_key",
    ]
    return language_rows.melt(
        id_vars=id_vars,
        value_vars=list(PRIMARY_METRICS),
        var_name="metric",
        value_name="value",
    ).dropna(subset=["value"])
