"""Regenerate language-correctness metric correlations from experiments.csv.

Usage:
    uv run python -m seatau.analysis.metric_correlations_by_language
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from paths import EXPERIMENTS_CSV, METRIC_CORRELATIONS_BY_LANGUAGE_CSV

LANGUAGE_METRICS = ("user_language_correctness", "agent_language_correctness")
OUTCOME_METRICS = ("pass_hat_1", "pass_hat_2", "pass_hat_3", "rho_3")
OUTPUT_COLUMNS = (
    "summary_level",
    "language_metric",
    "outcome_metric",
    "n",
    "pearson_r",
    "r_squared",
    "scenario",
    "domain",
)


def _normalize_experiment_rows(experiments_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(experiments_csv)
    df.columns = [col.strip() for col in df.columns]
    if "rho_3" not in df.columns and "rho_hat_3" in df.columns:
        df["rho_3"] = df["rho_hat_3"]
    for column in (*LANGUAGE_METRICS, *OUTCOME_METRICS):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _correlation_row(
    frame: pd.DataFrame,
    *,
    summary_level: str,
    language_metric: str,
    outcome_metric: str,
    scenario: str | None = None,
    domain: str | None = None,
) -> dict[str, float | int | str | None]:
    pair = frame[[language_metric, outcome_metric]].dropna()
    n = len(pair)
    if (
        n < 2
        or pair[language_metric].nunique() < 2
        or pair[outcome_metric].nunique() < 2
    ):
        pearson_r = np.nan
    else:
        pearson_r = float(pair[language_metric].corr(pair[outcome_metric]))
    return {
        "summary_level": summary_level,
        "language_metric": language_metric,
        "outcome_metric": outcome_metric,
        "n": n,
        "pearson_r": pearson_r,
        "r_squared": pearson_r * pearson_r if not np.isnan(pearson_r) else np.nan,
        "scenario": scenario,
        "domain": domain,
    }


def _metric_rows(
    frame: pd.DataFrame,
    *,
    summary_level: str,
    scenario: str | None = None,
    domain: str | None = None,
) -> Iterable[dict[str, float | int | str | None]]:
    for language_metric in LANGUAGE_METRICS:
        for outcome_metric in OUTCOME_METRICS:
            yield _correlation_row(
                frame,
                summary_level=summary_level,
                language_metric=language_metric,
                outcome_metric=outcome_metric,
                scenario=scenario,
                domain=domain,
            )


def build_metric_correlations_by_language(experiments_csv: Path) -> pd.DataFrame:
    """Build Pearson correlations for language correctness versus outcomes."""

    df = _normalize_experiment_rows(experiments_csv)
    rows: list[dict[str, float | int | str | None]] = []
    rows.extend(_metric_rows(df, summary_level="overall"))

    for scenario, group in df.groupby("scenario", sort=False, dropna=False):
        rows.extend(
            _metric_rows(group, summary_level="scenario", scenario=str(scenario))
        )

    for domain, group in df.groupby("domain", sort=False, dropna=False):
        rows.extend(_metric_rows(group, summary_level="domain", domain=str(domain)))

    for (scenario, domain), group in df.groupby(
        ["scenario", "domain"], sort=False, dropna=False
    ):
        rows.extend(
            _metric_rows(
                group,
                summary_level="scenario_domain",
                scenario=str(scenario),
                domain=str(domain),
            )
        )

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def write_metric_correlations_by_language(
    experiments_csv: Path,
    output: Path,
) -> Path:
    """Write regenerated metric correlations and return the output path."""

    output.parent.mkdir(parents=True, exist_ok=True)
    df = build_metric_correlations_by_language(experiments_csv)
    df.to_csv(output, index=False, float_format="%.6f", na_rep="")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=EXPERIMENTS_CSV)
    parser.add_argument(
        "--output", type=Path, default=METRIC_CORRELATIONS_BY_LANGUAGE_CSV
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = write_metric_correlations_by_language(args.experiments_csv, args.output)
    print(output)


if __name__ == "__main__":
    main()
