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
OPENROUTER_KEY_ENV_NAMES = (
    "OPENROUTER_API_KEY",
    "OPENROUTER_API_KEY_SEACROWD",
    "OPENROUTER_API_KEY_ALGOVERSE",
)


@dataclass(frozen=True)
class OpenRouterKeySnapshot:
    """Snapshot of one configured OpenRouter API key."""

    env_name: str
    limit: OpenRouterKeyLimit | None


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


def _candidate_openrouter_key_envs() -> list[str]:
    """Return configured OpenRouter API key env names in priority order."""
    _load_dotenv()
    candidates: list[str] = []
    for env_name in OPENROUTER_KEY_ENV_NAMES:
        if os.getenv(env_name, "").strip():
            candidates.append(env_name)
    prefix = "OPENROUTER_API_KEY_"
    for env_name in sorted(os.environ):
        if (
            env_name.startswith(prefix)
            and env_name not in candidates
            and os.getenv(env_name, "").strip()
        ):
            candidates.append(env_name)
    return candidates


def _fetch_openrouter_key_limit_for_env(
    api_key_env: str,
) -> OpenRouterKeyLimit | None:
    """Fetch the OpenRouter key balance snapshot for one env var."""
    api_key = os.getenv(api_key_env, "").strip()
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


def fetch_openrouter_key_snapshots() -> list[OpenRouterKeySnapshot]:
    """Fetch snapshots for all configured OpenRouter API keys."""
    snapshots: list[OpenRouterKeySnapshot] = []
    for env_name in _candidate_openrouter_key_envs():
        snapshots.append(
            OpenRouterKeySnapshot(
                env_name=env_name,
                limit=_fetch_openrouter_key_limit_for_env(env_name),
            ),
        )
    return snapshots


def fetch_openrouter_key_limit(
    api_key_env: str = "OPENROUTER_API_KEY",
) -> OpenRouterKeyLimit | None:
    """Fetch the current OpenRouter key balance snapshot.

    Returns ``None`` when the key is unset, the account has no limit, or the
    API request fails.
    """
    _load_dotenv()
    return _fetch_openrouter_key_limit_for_env(api_key_env)


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
    api_key_env: str | None = None,
    limit: OpenRouterKeyLimit | None = None,
    message: str | None = None,
    process_name: str | None = None,
    delta: dict[str, float] | None = None,
) -> str:
    """Render a parseable OpenRouter limit record."""
    payload: dict[str, object] = {}
    if api_key_env is not None:
        payload["api_key_env"] = api_key_env
    payload.update(
        {
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
    )
    if process_name is not None:
        payload["process_name"] = process_name
    if message is not None:
        payload["message"] = message
    if delta is not None:
        payload["delta"] = delta
    if limit is not None:
        payload.update(limit.as_payload())
    return "\n".join(_format_lines(payload))


def _format_openrouter_key_limit_blocks(
    snapshots: list[OpenRouterKeySnapshot],
    *,
    phase: str,
    status_if_missing: str,
    process_name: str | None = None,
    message_if_missing: str,
    message_if_ok: str | None = None,
) -> list[str]:
    """Render one block per configured OpenRouter API key."""
    blocks: list[str] = []
    for snapshot in snapshots:
        if snapshot.limit is None:
            blocks.append(
                _format_openrouter_key_limit(
                    phase=phase,
                    status=status_if_missing,
                    api_key_env=snapshot.env_name,
                    process_name=process_name,
                    message=message_if_missing,
                )
            )
            continue
        blocks.append(
            _format_openrouter_key_limit(
                phase=phase,
                status="ok",
                api_key_env=snapshot.env_name,
                process_name=process_name,
                limit=snapshot.limit,
                message=message_if_ok,
            )
        )
    return blocks


def print_openrouter_key_limit() -> OpenRouterKeyLimit | None:
    """Print the current OpenRouter key balance snapshot(s)."""
    snapshots = fetch_openrouter_key_snapshots()
    if not snapshots:
        print(
            _format_openrouter_key_limit(
                phase="snapshot",
                status="missing_api_key",
                message="No OpenRouter API keys are set",
            ),
        )
        return None

    first_snapshot: OpenRouterKeyLimit | None = None
    blocks = _format_openrouter_key_limit_blocks(
        snapshots,
        phase="snapshot",
        status_if_missing="unavailable",
        message_if_missing="OpenRouter key limit is unavailable",
    )
    for block, snapshot in zip(blocks, snapshots, strict=True):
        if snapshot.limit is not None and first_snapshot is None:
            first_snapshot = snapshot.limit
        print(block)
        if snapshot is not snapshots[-1]:
            print("---")
    if first_snapshot is None:
        return None
    return first_snapshot


@contextmanager
def maybe_track_openrouter_cost(process_name: str) -> Iterator[None]:
    """Print OpenRouter balance before and after a process when enabled."""
    if not should_track_openrouter_cost():
        yield
        return

    before = fetch_openrouter_key_snapshots()
    if not before:
        print(
            _format_openrouter_key_limit(
                phase="before",
                status="unavailable",
                process_name=process_name,
                message=(
                    "OpenRouter cost tracking enabled, but no OpenRouter API keys "
                    "were found."
                ),
            ),
        )
    else:
        before_blocks = _format_openrouter_key_limit_blocks(
            before,
            phase="before",
            status_if_missing="unavailable",
            process_name=process_name,
            message_if_missing="OpenRouter key limit is unavailable",
        )
        for idx, block in enumerate(before_blocks):
            print(block)
            if idx < len(before_blocks) - 1:
                print("---")
    try:
        yield
    finally:
        after = fetch_openrouter_key_snapshots()
        if not after:
            print(
                _format_openrouter_key_limit(
                    phase="after",
                    status="unavailable",
                    process_name=process_name,
                    message="OpenRouter cost tracking enabled, but no OpenRouter API keys were found.",
                ),
            )
        else:
            before_by_env = {snapshot.env_name: snapshot.limit for snapshot in before}
            after_blocks = _format_openrouter_key_limit_blocks(
                after,
                phase="after",
                status_if_missing="unavailable",
                process_name=process_name,
                message_if_missing="OpenRouter key limit is unavailable",
            )
            for idx, (block, snapshot) in enumerate(zip(after_blocks, after, strict=True)):
                print(block)
                if snapshot.limit is None:
                    if idx < len(after_blocks) - 1:
                        print("---")
                    continue
                before_limit = before_by_env.get(snapshot.env_name)
                if before_limit is None:
                    print(
                        _format_openrouter_key_limit(
                            phase="delta",
                            status="unavailable",
                            api_key_env=snapshot.env_name,
                            process_name=process_name,
                            message=(
                                "Delta unavailable because before snapshot was "
                                "unavailable."
                            ),
                        ),
                    )
                    if idx < len(after_blocks) - 1:
                        print("---")
                    continue
                print(
                    _format_openrouter_key_limit(
                        phase="delta",
                        status="ok",
                        api_key_env=snapshot.env_name,
                        process_name=process_name,
                        delta={
                            "usage_against_limit": (
                                snapshot.limit.usage_against_limit
                                - before_limit.usage_against_limit
                            ),
                            "limit_remaining": (
                                snapshot.limit.limit_remaining - before_limit.limit_remaining
                            ),
                        },
                    ),
                )
                if idx < len(after_blocks) - 1:
                    print("---")


if __name__ == "__main__":
    print_openrouter_key_limit()
