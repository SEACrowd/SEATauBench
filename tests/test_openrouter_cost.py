from __future__ import annotations

import pytest

from utils import openrouter_cost


def test_format_openrouter_key_limit() -> None:
    snapshot = openrouter_cost.OpenRouterKeyLimit(
        limit_total=10.0,
        limit_remaining=7.5,
        usage_total=2.5,
        usage_against_limit=1.25,
        limit_reset="monthly",
    )

    assert openrouter_cost.format_openrouter_key_limit(snapshot) == (
        "OpenRouter key limits: "
        "limit=$10.00, "
        "used_total=$2.50, "
        "used_against_limit=$1.25, "
        "reset=monthly, "
        "remaining=$7.50"
    )


def test_print_openrouter_key_limit_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(openrouter_cost, "load_dotenv", lambda: None)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    snapshot = openrouter_cost.print_openrouter_key_limit()

    assert snapshot is None
    assert capsys.readouterr().out.strip() == "OPENROUTER_API_KEY is not set"


def test_maybe_track_openrouter_cost_prints_before_and_after(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(openrouter_cost.TRACK_COST_ENV, "1")
    snapshots = iter(
        [
            openrouter_cost.OpenRouterKeyLimit(
                limit_total=10.0,
                limit_remaining=8.0,
                usage_total=2.0,
                usage_against_limit=1.0,
                limit_reset="monthly",
            ),
            openrouter_cost.OpenRouterKeyLimit(
                limit_total=10.0,
                limit_remaining=7.5,
                usage_total=2.5,
                usage_against_limit=1.5,
                limit_reset="monthly",
            ),
        ]
    )
    monkeypatch.setattr(
        openrouter_cost,
        "fetch_openrouter_key_limit",
        lambda: next(snapshots),
    )

    with openrouter_cost.maybe_track_openrouter_cost("translation"):
        pass

    out = capsys.readouterr().out
    assert "[translation] OpenRouter key limits before:" in out
    assert "[translation] OpenRouter key limits after:" in out
    assert "[translation] Delta: used_against_limit=+0.50, remaining=-0.50" in out
