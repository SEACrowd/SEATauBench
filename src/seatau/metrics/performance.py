"""Performance metric helpers for SEATauBench summaries."""

from __future__ import annotations

from math import comb

DOMAIN_TOTALS = {"airline": 150, "retail": 342, "telecom": 342}


def pass_at_k(task_rewards: list[list[float]], k: int) -> float | None:
    """Compute mean pass^k from per-task trial rewards.

    Args:
        task_rewards: Reward values grouped by task id.
        k: Number of successful trials required.

    Returns:
        Rounded mean pass^k, or None when no task has at least k trials.
    """
    values: list[float] = []
    for rewards in task_rewards:
        num_trials = len(rewards)
        if num_trials < k:
            continue
        success_count = sum(reward == 1.0 for reward in rewards)
        values.append(comb(success_count, k) / comb(num_trials, k))
    return mean(values)


def ratio(numerator: float, denominator: float) -> float | None:
    """Return a rounded ratio, or None for a zero denominator."""
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def mean(values: list[float]) -> float | None:
    """Return a rounded arithmetic mean, or None for an empty list."""
    return round(sum(values) / len(values), 3) if values else None


def rho(pass_hat_1: float | None, pass_hat_3: float | None) -> float | None:
    """Compute rho_hat_3 as pass_hat_3 / pass_hat_1."""
    if not pass_hat_1 or pass_hat_3 is None:
        return None
    return round(pass_hat_3 / pass_hat_1, 3)
