from __future__ import annotations

import json
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
