"""Shared statistical helpers for SEATauBench analyses."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

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
