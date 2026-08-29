"""Language-correctness evaluator for tau2 simulation runs."""

from __future__ import annotations

from collections.abc import Callable

from seatau.metrics.language_use import (
    compute_simulation_language_correctness,
)
from seatau.metrics.language_use import (
    infer_expected_assistant_language as _infer_expected_assistant_language,
)
from tau2.data_model.simulation import SimulationRun


def infer_expected_assistant_language(
    *,
    lang_id: str | None,
    lang_components: list[str] | set[str] | None,
    seatau_experiment: str | None,
) -> str:
    """Infer assistant target language from SEA-Tau scenario metadata."""
    return _infer_expected_assistant_language(
        lang_id=lang_id,
        lang_components=lang_components,
        scenario=seatau_experiment,
    )


def compute_language_correctness(
    *,
    simulation: SimulationRun,
    lang_id: str | None,
    lang_components: list[str] | set[str] | None,
    seatau_experiment: str | None,
    language_detector: Callable[[str], str | None] | None = None,
) -> dict:
    """Compute proportion of assistant turns in the expected language."""
    return compute_simulation_language_correctness(
        simulation=simulation,
        role="assistant",
        lang_id=lang_id,
        lang_components=lang_components,
        scenario=seatau_experiment,
        language_detector=language_detector,
    )
