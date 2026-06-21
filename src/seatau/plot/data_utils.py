"""Data loading, filtering, normalization, and deduplication for SEA-TauBench plots."""

from pathlib import Path

import numpy as np
import pandas as pd

from seatau.plot.config import (
    FILTER_SETTING,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_LABELS,
    METRIC_RENAMES,
    MODEL_LABELS,
    PRIMARY_METRICS,
    SCENARIO_ID_BY_NAME,
    SCENARIO_LABELS,
)


def normalize_key_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def parse_scenario_id(series: pd.Series) -> pd.Series:
    """Map canonical scenario names to stable numeric ids."""
    return series.astype("string").str.strip().map(SCENARIO_ID_BY_NAME).astype("Int64")


def load_and_prepare(
    csv_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Load, normalize, filter, and deduplicate the experiments CSV.

    Args:
        csv_path: Path to experiments_all.csv.

    Returns:
        Tuple of (raw_df, normalized_df, clean_df, duplicate_summary, audit_dict).
        clean_df has exactly one row per (scenario, domain, language, model) combo.
    """
    raw = pd.read_csv(csv_path)
    raw.columns = [col.strip() for col in raw.columns]
    df = raw.reset_index(names="source_row").copy()

    for csv_col, metric_key in METRIC_RENAMES.items():
        if csv_col in df.columns:
            df[metric_key] = pd.to_numeric(df[csv_col], errors="coerce")
        else:
            df[metric_key] = np.nan

    df["scenario_raw"] = df["scenario"].astype("string").str.strip()
    df["scenario_id"] = parse_scenario_id(df["scenario_raw"])
    df["scenario_label"] = df["scenario_raw"].map(SCENARIO_LABELS).fillna(
        df["scenario_raw"]
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

    has_primary_metric = df[PRIMARY_METRICS].notna().any(axis=1)
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
