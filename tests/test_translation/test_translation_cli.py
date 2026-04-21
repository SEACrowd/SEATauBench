from __future__ import annotations

import pytest
from click.core import ParameterSource
from click.testing import CliRunner

from translation.cli import _resolve_api_base, _resolve_model, cli
from translation.config import DEFAULT_VERTEX_MODEL, OPENROUTER_API_BASE


def test_resolve_api_base_prefers_explicit_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LITELLM_API_BASE", "https://env-proxy.example/v1")

    resolved = _resolve_api_base(
        model="openai/gpt-5.4-mini",
        api_base="https://explicit-proxy.example/v1",
    )

    assert resolved == "https://explicit-proxy.example/v1"


def test_resolve_api_base_uses_env_proxy_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LITELLM_API_BASE", "https://env-proxy.example/v1")

    resolved = _resolve_api_base(model="openai/gpt-5.4-mini", api_base=None)

    assert resolved == "https://env-proxy.example/v1"


def test_resolve_api_base_defaults_openrouter_for_openrouter_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)

    resolved = _resolve_api_base(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        api_base=None,
    )

    assert resolved == OPENROUTER_API_BASE


def test_resolve_api_base_leaves_openai_models_unset_without_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)

    resolved = _resolve_api_base(model="openai/gpt-5.4-mini", api_base=None)

    assert resolved is None


def test_resolve_model_prefers_vertex_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERTEXAI_PROJECT", "sea-tau")

    resolved = _resolve_model(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        model_source=ParameterSource.DEFAULT,
    )

    assert resolved == DEFAULT_VERTEX_MODEL


def test_resolve_model_keeps_explicit_model_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERTEXAI_PROJECT", "sea-tau")

    resolved = _resolve_model(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        model_source=ParameterSource.COMMANDLINE,
    )

    assert resolved == "openrouter/google/gemini-3.1-flash-lite-preview"


def test_resolve_model_normalizes_vertex_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VERTEXAI_PROJECT", raising=False)

    resolved = _resolve_model(
        model="vertex-ai/gemini-3-1-flash-lite-preview",
        model_source=ParameterSource.COMMANDLINE,
    )

    assert resolved == DEFAULT_VERTEX_MODEL


def test_help_mentions_vertex_auto_default() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert DEFAULT_VERTEX_MODEL in result.output
