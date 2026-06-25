"""Regenerate ``data/analyses/perf_by_language.csv``.

Usage:
    uv run python -m seatau.analysis.perf_by_language
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from paths import EXPERIMENTS_CSV, PERF_BY_LANGUAGE_CSV
from seatau.analysis.experiment_metrics import clean_language_metric_rows
from seatau.analysis.stats import (
    DEFAULT_BOOTSTRAP_SAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    bootstrap_mean_ci,
)


def build_perf_by_language(
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


def write_perf_by_language(
    experiments_csv: Path,
    output: Path = PERF_BY_LANGUAGE_CSV,
    *,
    bootstraps: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> Path:
    """Write regenerated perf-by-language data and return the output path."""

    output.parent.mkdir(parents=True, exist_ok=True)
    build_perf_by_language(
        experiments_csv,
        bootstraps=bootstraps,
        seed=seed,
    ).to_csv(output, index=False, float_format="%.6f")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=EXPERIMENTS_CSV)
    parser.add_argument("--output", type=Path, default=PERF_BY_LANGUAGE_CSV)
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        write_perf_by_language(
            args.experiments_csv,
            args.output,
            bootstraps=args.bootstraps,
            seed=args.seed,
        )
    )


if __name__ == "__main__":
    main()
