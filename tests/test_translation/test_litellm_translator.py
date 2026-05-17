from __future__ import annotations

import json
import os
import sys
import types
from types import SimpleNamespace

import pytest

from translation.litellm_translator import LiteLLMTranslator
from translation.models import TranslationRequest


def _requests_from_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    user_message = next(msg["content"] for msg in messages if msg["role"] == "user")
    marker = "Input items JSON:\n"
    payload = user_message.split(marker, 1)[1]
    return json.loads(payload)


def _response(translations: list[dict[str, str]]) -> SimpleNamespace:
    content = json.dumps({"translations": translations})
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def test_build_messages_includes_preserve_human_names_instruction() -> None:
    translator = LiteLLMTranslator(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    messages = translator._build_messages(
        requests=[TranslationRequest(segment_id="id_1", text="John Smith called.")],
        source_language="English",
        target_language="Vietnamese",
    )

    system_message = next(msg["content"] for msg in messages if msg["role"] == "system")
    assert "Do not translate personal human names." in system_message


def test_build_messages_only_surfaces_relevant_protected_terms() -> None:
    translator = LiteLLMTranslator(
        model="openai/gpt-5.4-mini",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    messages = translator._build_messages(
        requests=[
            TranslationRequest(
                segment_id="id_1",
                text="Flight status is available and cabin is economy.",
            )
        ],
        source_language="English",
        target_language="Vietnamese",
        protected_terms={"available", "economy", "gift_card", "cancelled"},
    )

    user_message = next(msg["content"] for msg in messages if msg["role"] == "user")

    assert "available" in user_message
    assert "economy" in user_message
    assert "gift_card" not in user_message
    assert "cancelled" not in user_message


def test_build_messages_for_literal_translation_allows_runtime_label_translation() -> (
    None
):
    translator = LiteLLMTranslator(
        model="openai/gpt-5.4-mini",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    messages = translator._build_messages(
        requests=[TranslationRequest(segment_id="id_1", text="pending")],
        source_language="English",
        target_language="Vietnamese",
        translate_runtime_labels=True,
    )

    system_message = next(msg["content"] for msg in messages if msg["role"] == "system")

    assert "Translate the label text itself naturally" in system_message
    assert "Do not paraphrase or localize exact runtime labels" not in system_message


def test_build_messages_include_literal_glossary_for_agent_facing_prose() -> None:
    translator = LiteLLMTranslator(
        model="openai/gpt-5.4-mini",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    messages = translator._build_messages(
        requests=[
            TranslationRequest(
                segment_id="id_1",
                text="Cancel a pending order.",
                literal_map={"pending": "đang chờ xử lý"},
            )
        ],
        source_language="English",
        target_language="Vietnamese",
    )

    system_message = next(msg["content"] for msg in messages if msg["role"] == "system")
    user_message = next(msg["content"] for msg in messages if msg["role"] == "user")

    assert "Exception for agent-facing translated prose" in system_message
    assert (
        "replace that source span with the localized label exactly once"
        in system_message
    )
    assert "pending -> đang chờ xử lý" in user_message


def test_translate_batch_recovers_missing_ids_with_targeted_single_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0

    def completion(**kwargs: object) -> SimpleNamespace:
        nonlocal call_count
        call_count += 1
        requests = _requests_from_messages(kwargs["messages"])
        if len(requests) == 2:
            return _response([{"id": requests[0]["id"], "text": "one_vi"}])
        return _response([{"id": requests[0]["id"], "text": "two_vi"}])

    fake_litellm = types.SimpleNamespace(drop_params=False, completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    translator = LiteLLMTranslator(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    requests = [
        TranslationRequest(segment_id="id_1", text="one"),
        TranslationRequest(segment_id="id_2", text="two"),
    ]

    out = translator.translate_batch(requests, "English", "Vietnamese")

    assert out == {"id_1": "one_vi", "id_2": "two_vi"}
    assert call_count == 2


def test_translate_batch_splits_failed_batch_instead_of_replaying_whole_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0

    def completion(**kwargs: object) -> SimpleNamespace:
        nonlocal call_count
        call_count += 1
        requests = _requests_from_messages(kwargs["messages"])
        if len(requests) > 1:
            raise RuntimeError("Temporary malformed JSON response")
        request = requests[0]
        return _response([{"id": request["id"], "text": f"{request['text']}_vi"}])

    fake_litellm = types.SimpleNamespace(drop_params=False, completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    translator = LiteLLMTranslator(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    requests = [
        TranslationRequest(segment_id="id_1", text="one"),
        TranslationRequest(segment_id="id_2", text="two"),
    ]

    out = translator.translate_batch(requests, "English", "Vietnamese")

    assert out == {"id_1": "one_vi", "id_2": "two_vi"}
    assert call_count == 3  # one failed batch call + two single-item recoveries


def test_translate_batch_does_not_split_on_auth_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_count = 0

    def completion(**kwargs: object) -> SimpleNamespace:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("401 Unauthorized")

    fake_litellm = types.SimpleNamespace(drop_params=False, completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    translator = LiteLLMTranslator(
        model="openrouter/google/gemini-3.1-flash-lite-preview",
        api_key="test-key",
        max_rpm=None,
        retries=1,
    )
    requests = [
        TranslationRequest(segment_id="id_1", text="one"),
        TranslationRequest(segment_id="id_2", text="two"),
    ]

    with pytest.raises(RuntimeError, match="Translation failed after retries"):
        translator.translate_batch(requests, "English", "Vietnamese")

    assert call_count == 1


def test_translate_batch_normalizes_vertex_alias_and_sets_global_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_model: str | None = None

    def completion(**kwargs: object) -> SimpleNamespace:
        nonlocal seen_model
        seen_model = str(kwargs["model"])
        return _response([{"id": "id_1", "text": "done"}])

    fake_litellm = types.SimpleNamespace(drop_params=False, completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    monkeypatch.delenv("VERTEXAI_LOCATION", raising=False)

    translator = LiteLLMTranslator(
        model="vertex-ai/gemini-3-1-flash-lite-preview",
        api_key="",
        max_rpm=None,
        retries=1,
    )

    out = translator.translate_batch(
        [TranslationRequest(segment_id="id_1", text="one")],
        "English",
        "Vietnamese",
    )

    assert out == {"id_1": "done"}
    assert seen_model == "vertex_ai/gemini-3.1-flash-lite-preview"
    assert os.environ["VERTEXAI_LOCATION"] == "global"


def test_request_kwargs_include_vertex_project_and_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERTEXAI_PROJECT", "sea-tau")
    monkeypatch.setenv("VERTEXAI_LOCATION", "global")

    translator = LiteLLMTranslator(
        model="vertex_ai/gemini-3.1-flash-lite-preview",
        api_key="",
        max_rpm=None,
        retries=1,
    )

    kwargs = translator._request_kwargs([{"role": "user", "content": "hello"}])

    assert kwargs["vertex_project"] == "sea-tau"
    assert kwargs["vertex_location"] == "global"


def test_request_kwargs_respect_explicit_api_base_for_vertex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERTEXAI_PROJECT", "sea-tau")
    monkeypatch.setenv("VERTEXAI_LOCATION", "global")

    translator = LiteLLMTranslator(
        model="vertex_ai/gemini-3.1-flash-lite-preview",
        api_key="",
        api_base="https://custom-proxy.example/v1",
        max_rpm=None,
        retries=1,
    )

    kwargs = translator._request_kwargs([{"role": "user", "content": "hello"}])

    assert kwargs["vertex_project"] == "sea-tau"
    assert kwargs["vertex_location"] == "global"
    assert kwargs["api_base"] == "https://custom-proxy.example/v1"
