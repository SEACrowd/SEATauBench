from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

from tau2.data_model.simulation import SimulationRun
from tau2.utils.utils import DATA_DIR

SEATAU_EN_SCENARIO = {
    "english",
    "l2_tools",
}
SEATAU_L2_SCENARIOS = {"l2_interaction", "l2_domain"}
DEFAULT_FASTTEXT_LID_MODEL_PATH = DATA_DIR / "models" / "lid.176.bin"
DEFAULT_FASTTEXT_LID_COMPRESSED_MODEL_PATH = DATA_DIR / "models" / "lid.176.ftz"


def _normalize_lang_code(code: str) -> str:
    normalized = code.replace("__label__", "").strip().lower()
    aliases = {
        "eng": "en",
        "ind": "id",
        "tgl": "tl",
        "tha": "th",
        "vie": "vi",
        "zho": "zh",
        "cmn": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh",
    }
    if normalized in aliases:
        return aliases[normalized]
    if "-" in normalized:
        return normalized.split("-", 1)[0]
    return normalized


def infer_expected_assistant_language(
    *,
    lang_id: Optional[str],
    lang_components: Optional[list[str] | set[str]],
    seatau_experiment: Optional[str],
) -> str:
    """Infer assistant target language from SEA-TAU scenarios and lang components."""
    scenario = seatau_experiment.lower() if seatau_experiment else None
    if scenario in SEATAU_EN_SCENARIO:
        return "en"
    if scenario in SEATAU_L2_SCENARIOS:
        return _normalize_lang_code(lang_id or "en")

    if lang_id is None:
        return "en"
    components = set(lang_components or [])
    if "agent_system" in components:
        return _normalize_lang_code(lang_id)
    return "en"


@lru_cache(maxsize=1)
def _load_fasttext_model() -> tuple[object | None, Optional[str]]:
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
        model = fasttext.load_model(str(path))
    except (OSError, ValueError) as exc:
        return None, f"Failed to load fastText model from {path}: {exc}"
    return model, None


def _detect_language_fasttext(text: str) -> tuple[Optional[str], Optional[str]]:
    model, error = _load_fasttext_model()
    if model is None:
        return None, error

    label = _predict_fasttext_label(model, text)
    if label is None:
        return None, "fastText returned no language label"
    return _normalize_lang_code(label), None


def _predict_fasttext_label(model: object, text: str) -> Optional[str]:
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


def _batch_detect_fasttext(model: object, texts: list[str]) -> list[Optional[str]]:
    sanitized = [t.replace("\n", " ").strip() for t in texts]
    non_empty_idx = [i for i, t in enumerate(sanitized) if t]
    results: list[Optional[str]] = [None] * len(texts)
    if not non_empty_idx:
        return results

    batch = [sanitized[i] for i in non_empty_idx]
    try:
        labels_list, _ = model.predict(batch, k=1)
        for i, labels in zip(non_empty_idx, labels_list):
            results[i] = labels[0] if labels else None
    except ValueError as exc:
        # NumPy 2.x fallback — same workaround as _predict_fasttext_label
        if "Unable to avoid copy" not in str(exc):
            raise
        for i, text in zip(non_empty_idx, batch):
            results[i] = _predict_fasttext_label(model, text)
    return results


def compute_language_correctness(
    *,
    simulation: SimulationRun,
    lang_id: Optional[str],
    lang_components: Optional[list[str] | set[str]],
    seatau_experiment: Optional[str],
    language_detector: Optional[Callable[[str], Optional[str]]] = None,
) -> dict:
    """Compute proportion of assistant turns in the expected language."""
    expected_language = infer_expected_assistant_language(
        lang_id=lang_id,
        lang_components=lang_components,
        seatau_experiment=seatau_experiment,
    )

    assistant_turns = [
        msg
        for msg in simulation.get_messages()
        if getattr(msg, "role", None) == "assistant"
        and getattr(msg, "content", None)
        and str(msg.content).strip()
    ]

    if not assistant_turns:
        return {
            "expected_language": expected_language,
            "assistant_turn_count": 0,
            "detected_turn_count": 0,
            "correct_turn_count": 0,
            "score": None,
            "note": "No assistant text turns found for language evaluation.",
        }

    total_turns = len(assistant_turns)
    texts = [str(msg.content).strip() for msg in assistant_turns]
    turn_indices = [
        msg.turn_idx if msg.turn_idx is not None else -1 for msg in assistant_turns
    ]

    if language_detector is not None:
        detected_langs = [language_detector(t) for t in texts]
    else:
        model, model_error = _load_fasttext_model()
        if model is None:
            return {
                "expected_language": expected_language,
                "assistant_turn_count": total_turns,
                "detected_turn_count": 0,
                "correct_turn_count": 0,
                "score": None,
                "note": "Language detection unavailable.",
                "detector_warning": model_error,
            }
        raw_labels = _batch_detect_fasttext(model, texts)
        detected_langs = [
            _normalize_lang_code(label) if label is not None else None
            for label in raw_labels
        ]

    detected_turn_count = 0
    correct_turn_count = 0
    incorrect_turn_indices: list[int] = []

    for turn_idx, detected in zip(turn_indices, detected_langs):
        if detected is None:
            incorrect_turn_indices.append(turn_idx)
            continue
        detected_turn_count += 1
        if _normalize_lang_code(detected) == expected_language:
            correct_turn_count += 1
        else:
            incorrect_turn_indices.append(turn_idx)

    score = correct_turn_count / total_turns
    return {
        "expected_language": expected_language,
        "assistant_turn_count": total_turns,
        "detected_turn_count": detected_turn_count,
        "correct_turn_count": correct_turn_count,
        "score": score,
        "incorrect_turn_indices": incorrect_turn_indices,
    }
