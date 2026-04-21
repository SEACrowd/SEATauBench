"""OpenRouter balance tracking helpers."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

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

    def as_payload(self) -> dict[str, object]:
        """Return a JSON-serializable payload for printing."""
        return {
            "limit_total": self.limit_total,
            "limit_remaining": self.limit_remaining,
            "usage_total": self.usage_total,
            "usage_against_limit": self.usage_against_limit,
            "limit_reset": self.limit_reset,
            "current_limit": self.limit_total,
            "current_cost": self.usage_against_limit,
        }


def _load_dotenv() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _format_value(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _format_lines(payload: dict[str, object], *, prefix: str = "") -> list[str]:
    lines: list[str] = []
    for key, value in payload.items():
        full_key = f"{prefix}{key}"
        if isinstance(value, dict):
            lines.extend(_format_lines(value, prefix=f"{full_key}."))
        else:
            lines.append(f"{full_key}: {_format_value(value)}")
    return lines


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
        f"current_limit=${limit.limit_total:.2f}, "
        f"current_cost=${limit.usage_against_limit:.2f}, "
        f"used_total=${limit.usage_total:.2f}, "
        f"reset={limit.limit_reset}, "
        f"remaining=${limit.limit_remaining:.2f}"
    )


def _format_openrouter_key_limit(
    *,
    phase: str,
    status: str,
    limit: OpenRouterKeyLimit | None = None,
    message: str | None = None,
    process_name: str | None = None,
    delta: dict[str, float] | None = None,
) -> str:
    """Render a parseable OpenRouter limit record."""
    payload: dict[str, object] = {
        "event": "openrouter_key_limit",
        "phase": phase,
        "status": status,
        "current_limit": None,
        "current_cost": None,
        "limit_total": None,
        "limit_remaining": None,
        "usage_total": None,
        "usage_against_limit": None,
        "limit_reset": None,
    }
    if process_name is not None:
        payload["process_name"] = process_name
    if message is not None:
        payload["message"] = message
    if delta is not None:
        payload["delta"] = delta
    if limit is not None:
        payload.update(limit.as_payload())
    return "\n".join(_format_lines(payload))


def print_openrouter_key_limit() -> OpenRouterKeyLimit | None:
    """Print the current OpenRouter key balance snapshot."""
    _load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(
            _format_openrouter_key_limit(
                phase="snapshot",
                status="missing_api_key",
                message="OPENROUTER_API_KEY is not set",
            ),
        )
        return None

    snapshot = fetch_openrouter_key_limit()
    if snapshot is None:
        print(
            _format_openrouter_key_limit(
                phase="snapshot",
                status="unavailable",
                message="OpenRouter key limit is unavailable",
            ),
        )
        return None

    print(
        _format_openrouter_key_limit(
            phase="snapshot",
            status="ok",
            limit=snapshot,
        ),
    )
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
            _format_openrouter_key_limit(
                phase="before",
                status="unavailable",
                process_name=process_name,
                message="OpenRouter cost tracking enabled, but no OpenRouter limit was found.",
            ),
        )
    else:
        print(
            _format_openrouter_key_limit(
                phase="before",
                status="ok",
                process_name=process_name,
                limit=before,
            ),
        )
    try:
        yield
    finally:
        after = fetch_openrouter_key_limit()
        if after is None:
            print(
                _format_openrouter_key_limit(
                    phase="after",
                    status="unavailable",
                    process_name=process_name,
                    message="OpenRouter key limit is unavailable",
                ),
            )
        else:
            print(
                _format_openrouter_key_limit(
                    phase="after",
                    status="ok",
                    process_name=process_name,
                    limit=after,
                ),
            )
            if before is None:
                print(
                    _format_openrouter_key_limit(
                        phase="delta",
                        status="unavailable",
                        process_name=process_name,
                        message="Delta unavailable because before snapshot was unavailable.",
                    ),
                )
            else:
                print(
                    _format_openrouter_key_limit(
                        phase="delta",
                        status="ok",
                        process_name=process_name,
                        delta={
                            "usage_against_limit": (
                                after.usage_against_limit - before.usage_against_limit
                            ),
                            "limit_remaining": after.limit_remaining
                            - before.limit_remaining,
                        },
                    ),
                )


if __name__ == "__main__":
    print_openrouter_key_limit()
