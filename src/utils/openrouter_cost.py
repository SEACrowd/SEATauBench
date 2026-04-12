"""OpenRouter balance tracking helpers.

These helpers mirror ``src/debug/cost.py`` but make the balance check reusable
from process entry points such as translation and simulation runs.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import requests

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dev dependency
    load_dotenv = None

TRACK_COST_ENV = "TAU2_TRACK_OPENROUTER_COST"


@dataclass(frozen=True)
class OpenRouterKeyLimit:
    """Snapshot of the OpenRouter key usage response."""

    limit_total: float
    limit_remaining: float
    usage_total: float
    usage_against_limit: float
    limit_reset: str


def _load_dotenv() -> None:
    if load_dotenv is not None:
        load_dotenv()


def should_track_openrouter_cost() -> bool:
    """Return whether OpenRouter balance tracking is enabled."""
    _load_dotenv()
    return os.getenv(TRACK_COST_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def fetch_openrouter_key_limit() -> OpenRouterKeyLimit | None:
    """Fetch the current OpenRouter key balance snapshot.

    Returns ``None`` when the key is unset, the account has no limit, or the
    API request fails.
    """
    _load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        key_data = response.json().get("data", {})
    except (requests.RequestException, ValueError, AttributeError, TypeError):
        return None

    if not key_data.get("limit"):
        return None

    limit_reset = key_data.get("limit_reset") or "monthly"
    usage_field = {
        "daily": "usage_daily",
        "weekly": "usage_weekly",
        "monthly": "usage_monthly",
    }.get(limit_reset, "usage")
    return OpenRouterKeyLimit(
        limit_total=float(key_data.get("limit") or 0),
        limit_remaining=float(key_data.get("limit_remaining") or 0),
        usage_total=float(key_data.get("usage") or 0),
        usage_against_limit=float(key_data.get(usage_field) or 0),
        limit_reset=str(limit_reset),
    )


def format_openrouter_key_limit(limit: OpenRouterKeyLimit) -> str:
    """Render a snapshot in the same style as ``src/debug/cost.py``."""
    return (
        "OpenRouter key limits: "
        f"limit=${limit.limit_total:.2f}, "
        f"used_total=${limit.usage_total:.2f}, "
        f"used_against_limit=${limit.usage_against_limit:.2f}, "
        f"reset={limit.limit_reset}, "
        f"remaining=${limit.limit_remaining:.2f}"
    )


def print_openrouter_key_limit() -> OpenRouterKeyLimit | None:
    """Print the current OpenRouter key balance snapshot."""
    _load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY is not set")
        return None

    snapshot = fetch_openrouter_key_limit()
    if snapshot is None:
        print("There's no OpenRouter key limit")
        return None

    print(format_openrouter_key_limit(snapshot))
    return snapshot


@contextmanager
def maybe_track_openrouter_cost(process_name: str) -> Iterator[None]:
    """Print OpenRouter balance before and after a process when enabled."""
    if not should_track_openrouter_cost():
        yield
        return

    before = fetch_openrouter_key_limit()
    if before is None:
        print(
            f"[{process_name}] OpenRouter cost tracking enabled, but no "
            "OpenRouter limit was found."
        )
        yield
        return

    print(f"[{process_name}] OpenRouter key limits before:")
    print(format_openrouter_key_limit(before))
    try:
        yield
    finally:
        after = fetch_openrouter_key_limit()
        if after is None:
            print(f"[{process_name}] OpenRouter key limits after: unavailable")
            return

        print(f"[{process_name}] OpenRouter key limits after:")
        print(format_openrouter_key_limit(after))
        print(
            f"[{process_name}] Delta: "
            f"used_against_limit={after.usage_against_limit - before.usage_against_limit:+.2f}, "
            f"remaining={after.limit_remaining - before.limit_remaining:+.2f}"
        )
