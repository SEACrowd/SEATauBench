from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from translation.config import FIXED_PROTECTED_TERMS, TASK_ONLY_PROTECTED_TERMS
from translation.models import (
    DEFAULT_MAX_RPM,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT_S,
    TranslationRequest,
)

_NON_RECOVERABLE_ERROR_MARKERS = (
    "default credentials were not found",
    "missing api key",
    "invalid api key",
    "unauthorized",
    "authentication",
    "forbidden",
    "permission denied",
)


def _extract_json_block(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("text"), str):
                    parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(content)


@dataclass
class LiteLLMTranslator:
    model: str
    api_key: str
    api_base: str | None = None
    api_version: str | None = None
    max_rpm: float | None = DEFAULT_MAX_RPM
    timeout_s: int = DEFAULT_TIMEOUT_S
    retries: int = DEFAULT_RETRIES
    _last_request_ts: float | None = None

    def _resolved_model(self) -> str:
        model = self.model.strip()
        if "/" in model:
            return model
        # Route plain Gemini names to Google AI Studio provider by default.
        # Example: gemini-3-flash-preview -> gemini/gemini-3-flash-preview
        if model.startswith("gemini-"):
            return f"gemini/{model}"
        return model

    def _build_messages(
        self,
        requests: list[TranslationRequest],
        source_language: str,
        target_language: str,
    ) -> list[dict[str, str]]:
        payload = [{"id": item.segment_id, "text": item.text} for item in requests]
        dnt = ", ".join(sorted(FIXED_PROTECTED_TERMS | TASK_ONLY_PROTECTED_TERMS))
        system = (
            "You are a professional translation engine.\n"
            "Rules:\n"
            "- Preserve meaning, intent, and tone.\n"
            "- __PH_N__ placeholders mask runtime-canonical English terms (status codes,\n"
            "  enum values, IDs, tool names). Reproduce them verbatim — never translate,\n"
            "  paraphrase, or drop them.\n"
            "- Do not add, remove, or rename placeholders.\n"
            "- Keep code-like tokens unchanged.\n"
            "- Do not paraphrase or localize exact runtime labels, even inside quotes.\n"
            '- Return only valid JSON: {"translations":[{"id":"<id>","text":"<translated_text>"}]}'
        )
        user = (
            f"Translate each item from {source_language} to {target_language}.\n\n"
            f"Do not translate these terms even if they appear unmasked: {dnt}\n\n"
            "Input items JSON:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _min_interval_seconds(self) -> float:
        if self.max_rpm is None or self.max_rpm <= 0:
            return 0.0
        return 60.0 / self.max_rpm

    def _sleep_if_needed(self) -> None:
        min_interval = self._min_interval_seconds()
        if min_interval <= 0:
            return
        now = time.monotonic()
        if self._last_request_ts is None:
            return
        elapsed = now - self._last_request_ts
        remaining = min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _mark_request_time(self) -> None:
        self._last_request_ts = time.monotonic()

    def _retry_delay(self, exc: Exception, attempt: int) -> float:
        """
        Combine provider hint with baseline pacing.
        Parses messages like: 'Please retry in 5.820044938s.'
        """
        min_interval = self._min_interval_seconds()
        fallback = max(min_interval, 1.5 * attempt)
        text = str(exc)
        match = re.search(r"Please retry in\s+([0-9]+(?:\.[0-9]+)?)s", text)
        if not match:
            return fallback
        try:
            hinted = float(match.group(1))
        except ValueError:
            return fallback
        return max(hinted, min_interval)

    def _request_kwargs(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._resolved_model(),
            "messages": messages,
            "timeout": self.timeout_s,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_version:
            kwargs["api_version"] = self.api_version
        return kwargs

    def _parse_translations(
        self,
        response: Any,
        requests: list[TranslationRequest],
        source_language: str,
        target_language: str,
        completion_fn: Callable[..., Any],
    ) -> dict[str, str]:
        content = response.choices[0].message.content
        text = _message_text(content)
        parsed = _extract_json_block(text)
        rows = parsed.get("translations", [])
        out = {
            str(row["id"]): str(row["text"])
            for row in rows
            if "id" in row and "text" in row
        }
        expected = {item.segment_id for item in requests}
        missing = expected - set(out.keys())
        if not missing:
            return out
        if len(requests) == 1:
            raise ValueError(f"Missing IDs in model response: {sorted(missing)}")
        missing_requests = [
            request for request in requests if request.segment_id in missing
        ]
        for request in missing_requests:
            out.update(
                self._translate_requests(
                    requests=[request],
                    source_language=source_language,
                    target_language=target_language,
                    completion_fn=completion_fn,
                )
            )
        return out

    def _should_split_after_failure(
        self,
        message: str,
        batch_size: int,
    ) -> bool:
        if batch_size <= 1:
            return False
        lowered = message.lower()
        return not any(marker in lowered for marker in _NON_RECOVERABLE_ERROR_MARKERS)

    def _translate_requests(
        self,
        requests: list[TranslationRequest],
        source_language: str,
        target_language: str,
        completion_fn: Callable[..., Any],
    ) -> dict[str, str]:
        messages = self._build_messages(
            requests=requests,
            source_language=source_language,
            target_language=target_language,
        )

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                self._sleep_if_needed()
                response = completion_fn(**self._request_kwargs(messages))
                self._mark_request_time()
                return self._parse_translations(
                    response=response,
                    requests=requests,
                    source_language=source_language,
                    target_language=target_language,
                    completion_fn=completion_fn,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self._retry_delay(exc, attempt))
                continue

        message = str(last_error) if last_error else "unknown error"
        if self._should_split_after_failure(message, batch_size=len(requests)):
            midpoint = len(requests) // 2
            left = self._translate_requests(
                requests=requests[:midpoint],
                source_language=source_language,
                target_language=target_language,
                completion_fn=completion_fn,
            )
            right = self._translate_requests(
                requests=requests[midpoint:],
                source_language=source_language,
                target_language=target_language,
                completion_fn=completion_fn,
            )
            return left | right

        if "default credentials were not found" in message.lower():
            raise RuntimeError(
                "LiteLLM is trying to use Vertex credentials (ADC), but none were found. "
                "Use a Gemini AI Studio route (e.g. model 'gemini/gemini-3-flash-preview' "
                "with --api-key-env GEMINI_API_KEY), or configure Vertex ADC."
            ) from last_error
        raise RuntimeError(f"Translation failed after retries: {last_error}")

    def translate_batch(
        self,
        requests: list[TranslationRequest],
        source_language: str,
        target_language: str,
    ) -> dict[str, str]:
        try:
            import litellm
            from litellm import completion
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "litellm is required for translation. Install project dependencies first."
            ) from exc
        litellm.drop_params = True

        return self._translate_requests(
            requests=requests,
            source_language=source_language,
            target_language=target_language,
            completion_fn=completion,
        )
