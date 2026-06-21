"""Language-use metrics backed by fastText language identification."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, cast

from seatau.constants import (
    DEFAULT_FASTTEXT_LID_COMPRESSED_MODEL_PATH,
    DEFAULT_FASTTEXT_LID_MODEL_PATH,
)
from seatau.experiment_matrix import get_scenario_lang_components

LanguageDetector = Callable[[str], str | None]


class FastTextModel(Protocol):
    """Subset of the fastText model interface used by this module."""

    f: Any

    def predict(self, text: str | list[str], k: int = 1) -> Any:
        """Predict language labels for one text value or a batch."""


def normalize_lang_code(code: str) -> str:
    """Normalize a fastText/ISO language code to lowercase code form."""
    normalized = code.replace("__label__", "").strip().lower()
    if "-" in normalized:
        return normalized.split("-", 1)[0]
    return normalized


def infer_expected_language(
    *,
    role: str,
    lang_id: str | None,
    lang_components: Sequence[str] | set[str] | None = None,
    scenario: str | None = None,
) -> str:
    """Infer expected natural language for a user or assistant text turn.

    Args:
        role: Message role, usually ``"user"`` or ``"assistant"``.
        lang_id: Target language code from run metadata.
        lang_components: Scenario language components. If omitted and a scenario
            is provided, components are read from ``scenarios.yaml``.
        scenario: Canonical SEATau scenario id.

    Returns:
        Expected normalized language code.
    """
    components = set(lang_components or ())
    if not components and scenario:
        components = set(get_scenario_lang_components(scenario))

    required_component = "user_system" if role == "user" else "agent_system"
    if required_component in components:
        return normalize_lang_code(lang_id or "en")
    return "en"


def infer_expected_assistant_language(
    *,
    lang_id: str | None,
    lang_components: Sequence[str] | set[str] | None,
    scenario: str | None,
) -> str:
    """Infer expected assistant language for a SEATau run."""
    return infer_expected_language(
        role="assistant",
        lang_id=lang_id,
        lang_components=lang_components,
        scenario=scenario,
    )


@lru_cache(maxsize=1)
def load_fasttext_model() -> tuple[FastTextModel | None, str | None]:
    """Load the configured fastText LID model once."""
    try:
        import fasttext  # type: ignore[import-not-found]
    except ImportError:
        return None, "fasttext is not installed"

    model_path = os.getenv("TAU2_FASTTEXT_LID_MODEL_PATH")
    if model_path:
        path = Path(model_path).expanduser()
    elif DEFAULT_FASTTEXT_LID_MODEL_PATH.exists():
        path = DEFAULT_FASTTEXT_LID_MODEL_PATH
    elif DEFAULT_FASTTEXT_LID_COMPRESSED_MODEL_PATH.exists():
        path = DEFAULT_FASTTEXT_LID_COMPRESSED_MODEL_PATH
    else:
        return (
            None,
            "TAU2_FASTTEXT_LID_MODEL_PATH is not set and no default fastText "
            f"LID model was found at {DEFAULT_FASTTEXT_LID_MODEL_PATH}.",
        )

    if not path.exists():
        return None, f"fastText model file not found at {path}"

    try:
        model = cast(FastTextModel, fasttext.load_model(str(path)))
    except (OSError, ValueError) as exc:
        return None, f"Failed to load fastText model from {path}: {exc}"
    return model, None


def predict_fasttext_label(model: FastTextModel, text: str) -> str | None:
    """Predict a raw fastText language label for one text value."""
    sanitized = text.replace("\n", " ").strip()
    if not sanitized:
        return None

    try:
        labels, _scores = model.predict(sanitized, k=1)
        return labels[0] if labels else None
    except ValueError as exc:
        # fasttext==0.9.3 can fail under NumPy 2.x when wrapping probabilities
        # with np.array(copy=False), even though the low-level prediction worked.
        if "Unable to avoid copy" not in str(exc) or not hasattr(model, "f"):
            raise

    predictions = model.f.predict(sanitized + "\n", 1, 0.0, "strict")  # type: ignore[attr-defined]
    if not predictions:
        return None
    _probability, label = predictions[0]
    return label


def batch_detect_fasttext(model: FastTextModel, texts: list[str]) -> list[str | None]:
    """Predict raw fastText language labels for a text batch."""
    sanitized = [text.replace("\n", " ").strip() for text in texts]
    non_empty_idx = [idx for idx, text in enumerate(sanitized) if text]
    results: list[str | None] = [None] * len(texts)
    if not non_empty_idx:
        return results

    batch = [sanitized[idx] for idx in non_empty_idx]
    try:
        labels_list, _ = model.predict(batch, k=1)
        for idx, labels in zip(non_empty_idx, labels_list):
            results[idx] = labels[0] if labels else None
    except ValueError as exc:
        if "Unable to avoid copy" not in str(exc):
            raise
        for idx, text in zip(non_empty_idx, batch):
            results[idx] = predict_fasttext_label(model, text)
    return results


def detect_language_fasttext(text: str) -> tuple[str | None, str | None]:
    """Detect one text's language with the configured fastText model."""
    model, error = load_fasttext_model()
    if model is None:
        return None, error

    label = predict_fasttext_label(model, text)
    if label is None:
        return None, "fastText returned no language label"
    return normalize_lang_code(label), None


def text_turns(messages: Sequence[Any], role: str) -> list[tuple[int, str]]:
    """Extract substantial text turns for a message role."""
    turns: list[tuple[int, str]] = []
    for idx, message in enumerate(messages):
        message_role = _message_value(message, "role")
        if message_role != role:
            continue
        content = str(_message_value(message, "content") or "").strip()
        if len(content) < 5 or (content.startswith("###") and content.endswith("###")):
            continue
        turn_idx = _message_value(message, "turn_idx")
        turns.append((int(turn_idx) if turn_idx is not None else idx, content))
    return turns


def compute_role_language_correctness(
    *,
    messages: Sequence[Any],
    role: str,
    expected_language: str,
    language_detector: LanguageDetector | None = None,
    detector_model: FastTextModel | None = None,
) -> dict[str, Any]:
    """Compute the proportion of text turns in the expected language."""
    turns = text_turns(messages, role)
    role_count_key = f"{_role_label(role)}_turn_count"

    if not turns:
        return {
            "expected_language": expected_language,
            role_count_key: 0,
            "detected_turn_count": 0,
            "correct_turn_count": 0,
            "score": None,
            "incorrect_turn_indices": [],
            "note": f"No {role} text turns found for language evaluation.",
        }

    turn_indices = [idx for idx, _ in turns]
    texts = [text for _, text in turns]
    if language_detector is not None:
        detected_langs = [
            normalize_lang_code(detected)
            if (detected := language_detector(text)) is not None
            else None
            for text in texts
        ]
    else:
        model = detector_model
        if model is None:
            model, model_error = load_fasttext_model()
            if model is None:
                return {
                    "expected_language": expected_language,
                    role_count_key: len(turns),
                    "detected_turn_count": 0,
                    "correct_turn_count": 0,
                    "score": None,
                    "note": "Language detection unavailable.",
                    "detector_warning": model_error,
                    "incorrect_turn_indices": turn_indices,
                }
        raw_labels = batch_detect_fasttext(model, texts)
        detected_langs = [
            normalize_lang_code(label) if label is not None else None
            for label in raw_labels
        ]

    detected_turn_count = 0
    correct_turn_count = 0
    incorrect_turn_indices: list[int] = []
    normalized_expected = normalize_lang_code(expected_language)

    for turn_idx, detected in zip(turn_indices, detected_langs):
        if detected is None:
            incorrect_turn_indices.append(turn_idx)
            continue
        detected_turn_count += 1
        if detected == normalized_expected:
            correct_turn_count += 1
        else:
            incorrect_turn_indices.append(turn_idx)

    score = correct_turn_count / len(turns)
    return {
        "expected_language": normalized_expected,
        role_count_key: len(turns),
        "detected_turn_count": detected_turn_count,
        "correct_turn_count": correct_turn_count,
        "score": score,
        "incorrect_turn_indices": incorrect_turn_indices,
    }


def compute_simulation_language_correctness(
    *,
    simulation: Any,
    role: str,
    lang_id: str | None,
    lang_components: Sequence[str] | set[str] | None = None,
    scenario: str | None = None,
    language_detector: LanguageDetector | None = None,
) -> dict[str, Any]:
    """Compute role language correctness for one simulation object or dict."""
    expected_language = infer_expected_language(
        role=role,
        lang_id=lang_id,
        lang_components=lang_components,
        scenario=scenario,
    )
    return compute_role_language_correctness(
        messages=_simulation_messages(simulation),
        role=role,
        expected_language=expected_language,
        language_detector=language_detector,
    )


def compute_run_language_scores(
    *,
    simulations: Sequence[Any],
    role: str,
    expected_language: str,
    detector_model: FastTextModel | None,
) -> list[float | None]:
    """Compute per-simulation role language scores with one batched detector pass."""
    simulation_turns = [
        text_turns(_simulation_messages(sim), role) for sim in simulations
    ]
    flat_texts: list[str] = []
    owners: list[int] = []
    for sim_idx, turns in enumerate(simulation_turns):
        for _turn_idx, text in turns:
            owners.append(sim_idx)
            flat_texts.append(text)

    if not flat_texts or detector_model is None:
        return [None for _ in simulations]

    labels = batch_detect_fasttext(detector_model, flat_texts)
    normalized_expected = normalize_lang_code(expected_language)
    correct_by_sim = [0 for _ in simulations]
    total_by_sim = [len(turns) for turns in simulation_turns]

    for sim_idx, label in zip(owners, labels):
        if label is not None and normalize_lang_code(label) == normalized_expected:
            correct_by_sim[sim_idx] += 1

    return [
        (correct / total if total else None)
        for correct, total in zip(correct_by_sim, total_by_sim)
    ]


def _simulation_messages(simulation: Any) -> Sequence[Any]:
    if hasattr(simulation, "get_messages"):
        return simulation.get_messages()
    if isinstance(simulation, dict):
        return simulation.get("messages") or []
    return getattr(simulation, "messages", None) or []


def _message_value(message: Any, key: str) -> Any:
    if isinstance(message, dict):
        return message.get(key)
    return getattr(message, key, None)


def _role_label(role: str) -> str:
    return "assistant" if role == "assistant" else role
