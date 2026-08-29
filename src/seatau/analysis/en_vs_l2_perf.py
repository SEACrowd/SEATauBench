"""Regenerate ``data/analyses/en_vs_l2_perf.csv``.

Usage:
    uv run python -m seatau.analysis.en_vs_l2_perf
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from paths import ANALYSES_DIR, EN_VS_L2_PERF_CSV, EXPERIMENTS_CSV
from seatau.analysis.experiment_metrics import clean_language_metric_rows
from seatau.analysis.stats import (
    DEFAULT_BOOTSTRAP_SAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    bootstrap_mean_ci,
)
from seatau.plot.config import METRIC_RENAMES

DEFAULT_RUN_UNCERTAINTY_CSV = ANALYSES_DIR / "statistical_rigor" / "run_uncertainty.csv"


def build_en_vs_l2_perf(
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


def write_en_vs_l2_perf(
    experiments_csv: Path,
    output: Path = EN_VS_L2_PERF_CSV,
    *,
    run_uncertainty_csv: Path | None = DEFAULT_RUN_UNCERTAINTY_CSV,
    bootstraps: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> Path:
    """Write regenerated English versus L2 data and return the output path."""

    output.parent.mkdir(parents=True, exist_ok=True)
    build_en_vs_l2_perf(
        experiments_csv,
        run_uncertainty_csv=run_uncertainty_csv,
        bootstraps=bootstraps,
        seed=seed,
    ).to_csv(output, index=False, float_format="%.6f")
    return output


def _metric_column(metric: str) -> str:
    inverse = {renamed: raw for raw, renamed in METRIC_RENAMES.items()}
    return inverse[metric]


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=EXPERIMENTS_CSV)
    parser.add_argument("--output", type=Path, default=EN_VS_L2_PERF_CSV)
    parser.add_argument(
        "--run-uncertainty-csv",
        type=Path,
        default=DEFAULT_RUN_UNCERTAINTY_CSV,
    )
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        write_en_vs_l2_perf(
            args.experiments_csv,
            args.output,
            run_uncertainty_csv=args.run_uncertainty_csv,
            bootstraps=args.bootstraps,
            seed=args.seed,
        )
    )


if __name__ == "__main__":
    main()
