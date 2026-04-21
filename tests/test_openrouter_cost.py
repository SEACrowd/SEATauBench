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
        "current_limit=$10.00, "
        "current_cost=$1.25, "
        "used_total=$2.50, "
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
    out = capsys.readouterr().out
    assert "event: openrouter_key_limit" in out
    assert "phase: snapshot" in out
    assert "status: missing_api_key" in out
    assert "message: OPENROUTER_API_KEY is not set" in out


def test_maybe_track_openrouter_cost_prints_before_and_after(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(openrouter_cost, "load_dotenv", lambda: None)
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
    assert "event: openrouter_key_limit" in out
    assert "process_name: translation" in out
    assert "phase: before" in out
    assert "phase: after" in out
    assert "phase: delta" in out
    assert "delta.usage_against_limit: 0.5" in out
    assert "delta.limit_remaining: -0.5" in out


def test_maybe_track_openrouter_cost_prints_after_when_before_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(openrouter_cost, "load_dotenv", lambda: None)
    monkeypatch.setenv(openrouter_cost.TRACK_COST_ENV, "1")
    snapshots = iter(
        [
            None,
            openrouter_cost.OpenRouterKeyLimit(
                limit_total=50.0,
                limit_remaining=39.0,
                usage_total=11.0,
                usage_against_limit=6.0,
                limit_reset="monthly",
            ),
        ]
    )
    monkeypatch.setattr(
        openrouter_cost,
        "fetch_openrouter_key_limit",
        lambda: next(snapshots),
    )

    with openrouter_cost.maybe_track_openrouter_cost("tau2 run"):
        pass

    out = capsys.readouterr().out
    assert "process_name: tau2 run" in out
    assert "phase: before" in out
    assert "status: unavailable" in out
    assert "phase: after" in out
    assert "phase: delta" in out
    assert (
        "message: Delta unavailable because before snapshot was unavailable." in out
    )
