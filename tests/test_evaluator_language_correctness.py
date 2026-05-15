from tau2.data_model.message import AssistantMessage, UserMessage
from tau2.data_model.simulation import SimulationRun, TerminationReason
from tau2.data_model.tasks import EvaluationCriteria, RewardType, Task, UserScenario
from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation
from tau2.evaluator.language_correctness import (
    compute_language_correctness,
    infer_expected_assistant_language,
)


def _make_simulation(*assistant_turns: str) -> SimulationRun:
    messages = []
    for idx, text in enumerate(assistant_turns):
        messages.append(UserMessage.text(f"user turn {idx}"))
        messages.append(AssistantMessage.text(text))
    return SimulationRun(
        id="sim-1",
        task_id="task-1",
        start_time="2026-01-01T00:00:00",
        end_time="2026-01-01T00:00:10",
        duration=10.0,
        termination_reason=TerminationReason.AGENT_STOP,
        messages=messages,
    )


def _make_task() -> Task:
    return Task(
        id="task-1",
        user_scenario=UserScenario(instructions="test"),
        evaluation_criteria=None,
    )


def test_infer_expected_language_from_seatau_matrix() -> None:
    assert (
        infer_expected_assistant_language(
            lang_id="en",
            lang_components=["mixed_tools"],
            seatau_experiment="mixed_tools",
            seatau_target_lang="vi",
        )
        == "en"
    )
    assert (
        infer_expected_assistant_language(
            lang_id="th",
            lang_components=["user_system", "agent_system"],
            seatau_experiment="crosslingual",
            seatau_target_lang="th",
        )
        == "th"
    )


def test_compute_language_correctness_uses_assistant_turn_proportion() -> None:
    simulation = _make_simulation("Hello there", "Xin chao")

    detected = {"Hello there": "en", "Xin chao": "vi"}

    info = compute_language_correctness(
        simulation=simulation,
        lang_id="en",
        lang_components=[],
        seatau_experiment="baseline",
        seatau_target_lang=None,
        language_detector=lambda text: detected[text],
    )

    assert info["assistant_turn_count"] == 2
    assert info["correct_turn_count"] == 1
    assert info["score"] == 0.5


def test_evaluate_simulation_attaches_language_correctness_to_reward_info() -> None:
    simulation = _make_simulation("Hello there")
    task = _make_task()

    reward_info = evaluate_simulation(
        simulation=simulation,
        task=task,
        evaluation_type=EvaluationType.ALL,
        solo_mode=False,
        domain="mock",
        lang_id="en",
        lang_components=[],
        seatau_experiment="baseline",
        seatau_target_lang=None,
    )

    assert reward_info.info is not None
    assert "language_correctness" in reward_info.info


def test_language_correctness_can_be_evaluated_as_reward(monkeypatch) -> None:
    monkeypatch.setattr(
        "tau2.evaluator.evaluator.compute_language_correctness",
        lambda **kwargs: {
            "expected_language": "en",
            "assistant_turn_count": 2,
            "detected_turn_count": 2,
            "correct_turn_count": 1,
            "score": 0.5,
            "incorrect_turn_indices": [1],
        },
    )
    simulation = _make_simulation("Hello there", "Xin chao")
    task = _make_task()

    reward_info = evaluate_simulation(
        simulation=simulation,
        task=task,
        evaluation_type=EvaluationType.LANGUAGE_CORRECTNESS,
        solo_mode=False,
        domain="mock",
        lang_id="en",
        lang_components=[],
        seatau_experiment="baseline",
        seatau_target_lang=None,
    )

    assert reward_info.reward == 0.5
    assert reward_info.reward_basis == [RewardType.LANGUAGE_CORRECTNESS]
    assert reward_info.reward_breakdown == {RewardType.LANGUAGE_CORRECTNESS: 0.5}


def test_all_evaluation_multiplies_explicit_language_correctness_basis(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "tau2.evaluator.evaluator.compute_language_correctness",
        lambda **kwargs: {
            "expected_language": "en",
            "assistant_turn_count": 2,
            "detected_turn_count": 2,
            "correct_turn_count": 1,
            "score": 0.5,
            "incorrect_turn_indices": [1],
        },
    )
    simulation = _make_simulation("Hello there", "Xin chao")
    task = Task(
        id="task-1",
        user_scenario=UserScenario(instructions="test"),
        evaluation_criteria=EvaluationCriteria(
            reward_basis=[RewardType.LANGUAGE_CORRECTNESS]
        ),
    )

    reward_info = evaluate_simulation(
        simulation=simulation,
        task=task,
        evaluation_type=EvaluationType.ALL,
        solo_mode=False,
        domain="mock",
        lang_id="en",
        lang_components=[],
        seatau_experiment="baseline",
        seatau_target_lang=None,
    )

    assert reward_info.reward == 0.5
    assert reward_info.reward_breakdown == {RewardType.LANGUAGE_CORRECTNESS: 0.5}
