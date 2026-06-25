"""Plot-local data builders for SEATauBench figures."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from seatau.plot.config import FILTER_SETTING, METRIC_RENAMES, PRIMARY_METRICS

DEFAULT_BOOTSTRAP_SAMPLES = 1000
DEFAULT_BOOTSTRAP_SEED = 20260625


def bootstrap_mean_ci(
    values: Sequence[float] | np.ndarray,
    *,
    n_bootstrap: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int | None = DEFAULT_BOOTSTRAP_SEED,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Estimate a mean and percentile bootstrap confidence interval."""

    arr = np.asarray(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return np.nan, np.nan, np.nan
    mean = float(np.mean(arr))
    if len(arr) == 1:
        return mean, mean, mean
    rng = np.random.default_rng(seed)
    samples = rng.choice(arr, size=(n_bootstrap, len(arr)), replace=True).mean(axis=1)
    return (
        mean,
        float(np.quantile(samples, alpha / 2)),
        float(np.quantile(samples, 1 - alpha / 2)),
    )


def _metric_column(metric: str) -> str:
    inverse = {renamed: raw for raw, renamed in METRIC_RENAMES.items()}
    return inverse[metric]


def _normalize_key_series(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def load_clean_experiments(csv_path: Path) -> pd.DataFrame:
    """Load filtered, deduplicated experiment-summary rows for plot builders."""

    raw = pd.read_csv(csv_path)
    raw.columns = [col.strip() for col in raw.columns]
    df = raw.reset_index(names="source_row").copy()

    for csv_col, metric_key in METRIC_RENAMES.items():
        if csv_col in df.columns:
            df[metric_key] = pd.to_numeric(df[csv_col], errors="coerce")
        else:
            df[metric_key] = np.nan

    df["scenario_raw"] = _normalize_key_series(df["scenario"])
    df["domain_key"] = _normalize_key_series(df["domain"])
    df["domain_label"] = df["domain_key"].str.title()
    df["language_key"] = _normalize_key_series(df["language_senario"])
    df["language_group"] = np.where(
        df["language_key"].str.startswith("tool_mix_", na=False),
        "tool_mix",
        "language",
    )
    df["model_key"] = _normalize_key_series(df["normalized_agent_llm"])

    has_primary_metric = df[list(PRIMARY_METRICS)].notna().any(axis=1)
    filter_mask = (
        df["scenario_raw"].isin(FILTER_SETTING["scenario"])
        & df["domain_key"].isin(FILTER_SETTING["domain"])
        & df["language_key"].isin(FILTER_SETTING["language_senario"])
        & df["model_key"].isin(FILTER_SETTING["normalized_agent_llm"])
    )
    dedupe_keys = ["scenario_raw", "domain_key", "language_key", "model_key"]
    return (
        df.loc[filter_mask & has_primary_metric]
        .sort_values("source_row")
        .drop_duplicates(dedupe_keys, keep="last")
        .sort_values("source_row")
        .reset_index(drop=True)
    )


def clean_language_metric_rows(experiments_csv: Path) -> pd.DataFrame:
    """Return long-form metric rows for natural-language experiment settings."""

    clean_df = load_clean_experiments(experiments_csv)
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


def build_perf_by_language_data(
    experiments_csv: Path,
    *,
    bootstraps: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Build radar-plot values and CIs over domain-level means."""

    long = clean_language_metric_rows(experiments_csv)
    domain_means = (
        long.groupby(
            ["domain_label", "model_key", "metric", "language_key"],
            observed=True,
            as_index=False,
        )["value"]
        .mean()
        .rename(columns={"value": "domain_mean"})
    )
    rows: list[dict[str, float | int | str]] = []
    for (metric, model, language), group in domain_means.groupby(
        ["metric", "model_key", "language_key"],
        sort=False,
    ):
        mean, low, high = bootstrap_mean_ci(
            group["domain_mean"].to_numpy(dtype=float),
            n_bootstrap=bootstraps,
            seed=seed,
        )
        rows.append(
            {
                "metric": metric,
                "model": model,
                "language": language,
                "estimate": mean,
                "ci_low": max(0.0, low),
                "ci_high": min(1.0, high),
                "n_domains": len(group),
                "n_bootstrap": bootstraps,
                "ci_method": "bootstrap over domain-level means",
            }
        )
    return pd.DataFrame(rows)


def build_en_vs_l2_perf_data(
    experiments_csv: Path,
    *,
    run_uncertainty_csv: Path | None = None,
    bootstraps: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> pd.DataFrame:
    """Build English/non-English plot values from experiment-summary rows."""

    long = clean_language_metric_rows(experiments_csv)
    run_uncertainty = _read_run_uncertainty(run_uncertainty_csv)

    language_means = (
        long.groupby(
            ["domain_label", "domain_key", "model_key", "metric", "language_key"],
            observed=True,
            as_index=False,
        )["value"]
        .mean()
        .rename(columns={"value": "language_mean"})
    )

    rows: list[dict[str, float | int | str]] = []
    group_cols = ["domain_label", "domain_key", "model_key", "metric"]
    for (domain_label, domain_key, model, metric), group in language_means.groupby(
        group_cols,
        sort=False,
    ):
        english = group.loc[group["language_key"].eq("english")]
        non_english = group.loc[~group["language_key"].eq("english")]
        if english.empty or non_english.empty:
            continue

        non_en_mean, non_en_low, non_en_high = bootstrap_mean_ci(
            non_english["language_mean"].to_numpy(dtype=float),
            n_bootstrap=bootstraps,
            seed=seed,
        )
        english_estimate = float(english["language_mean"].iloc[0])
        english_low, english_high, english_method = _english_interval(
            run_uncertainty,
            domain_key=domain_key,
            model=model,
            metric=metric,
            estimate=english_estimate,
        )

        rows.append(
            {
                "domain": domain_label,
                "domain_key": domain_key,
                "model": model,
                "metric": metric,
                "english_estimate": english_estimate,
                "english_ci_low": max(0.0, english_low),
                "english_ci_high": min(1.0, english_high),
                "non_english_estimate": non_en_mean,
                "non_english_ci_low": max(0.0, non_en_low),
                "non_english_ci_high": min(1.0, non_en_high),
                "n_non_english_languages": len(non_english),
                "n_bootstrap": bootstraps,
                "english_ci_method": english_method,
                "non_english_ci_method": "bootstrap over non-English language means",
            }
        )
    return pd.DataFrame(rows)


def _read_run_uncertainty(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    run_uncertainty = pd.read_csv(path)
    run_uncertainty["plot_metric"] = run_uncertainty["metric"].map(METRIC_RENAMES)
    return run_uncertainty.dropna(subset=["plot_metric"])


def _english_interval(
    run_uncertainty: pd.DataFrame,
    *,
    domain_key: str,
    model: str,
    metric: str,
    estimate: float,
) -> tuple[float, float, str]:
    if run_uncertainty.empty:
        return estimate, estimate, "point estimate only"

    metric_column = _metric_column(metric)
    match = run_uncertainty.loc[
        run_uncertainty["scenario"].eq("english")
        & run_uncertainty["language"].eq("english")
        & run_uncertainty["domain"].eq(domain_key)
        & run_uncertainty["model"].eq(model)
        & run_uncertainty["metric"].eq(metric_column)
    ]
    if match.empty:
        return estimate, estimate, "point estimate only"
    return (
        float(match["ci_low"].iloc[0]),
        float(match["ci_high"].iloc[0]),
        "task-level bootstrap",
    )
