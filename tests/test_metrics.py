import pytest

from tau2.data_model.simulation import (
    Info,
    Results,
    SimulationRun,
    TerminationReason,
    UserInfo,
)
from tau2.data_model.tasks import EvaluationCriteria, Task, UserScenario
from tau2.environment.environment import EnvironmentInfo
from tau2.metrics.agent_metrics import compute_metrics, pass_hat_k


def _make_info(num_trials: int) -> Info:
    return Info(
        git_commit="abc123",
        num_trials=num_trials,
        max_steps=100,
        max_errors=10,
        user_info=UserInfo(implementation="user_simulator"),
        agent_info={"implementation": "llm_agent"},
        environment_info=EnvironmentInfo(domain_name="mock", policy="test policy"),
    )


def _make_task(task_id: str, *, evaluation_criteria: EvaluationCriteria | None) -> Task:
    return Task(
        id=task_id,
        user_scenario=UserScenario(instructions="test instruction"),
        evaluation_criteria=evaluation_criteria,
    )


def _make_sim(
    task_id: str,
    *,
    trial: int,
    reward: float,
    termination_reason: TerminationReason = TerminationReason.USER_STOP,
) -> SimulationRun:
    return SimulationRun(
        id=f"sim-{task_id}-t{trial}",
        task_id=task_id,
        start_time="2026-01-01T00:00:00",
        end_time="2026-01-01T00:01:00",
        duration=60.0,
        termination_reason=termination_reason,
        reward_info={
            "reward": reward,
            "db_check": None,
            "env_assertions": None,
            "action_checks": None,
            "nl_assertions": None,
            "communicate_checks": None,
            "reward_basis": None,
            "reward_breakdown": None,
        },
        agent_cost=0.0,
        messages=[],
        trial=trial,
        seed=42,
    )


def test_pass_hat_k_handles_edge_cases() -> None:
    assert pass_hat_k(1, 1, 1) == 1.0
    assert pass_hat_k(1, 0, 1) == 0.0
    assert pass_hat_k(2, 1, 1) == 0.5
    assert pass_hat_k(2, 1, 2) == 0.0

    with pytest.raises(ValueError):
        pass_hat_k(1, 1, 2)


def test_compute_metrics_uses_pass_one_for_failed_second_trial() -> None:
    results = Results(
        info=_make_info(num_trials=2),
        tasks=[
            _make_task(
                "task-1",
                evaluation_criteria=EvaluationCriteria(
                    actions=[],
                    env_assertions=[],
                    communicate_info=[],
                    nl_assertions=[],
                ),
            )
        ],
        simulations=[
            _make_sim("task-1", trial=0, reward=1.0),
            _make_sim("task-1", trial=1, reward=0.0),
        ],
    )

    metrics = compute_metrics(results)

    assert metrics.pass_hat_ks[1] == 0.5
    assert metrics.pass_hat_ks[2] == 0.0


def test_compute_metrics_exposes_pass_two_only_with_two_trials() -> None:
    single_trial_results = Results(
        info=_make_info(num_trials=1),
        tasks=[_make_task("task-1", evaluation_criteria=EvaluationCriteria())],
        simulations=[_make_sim("task-1", trial=0, reward=1.0)],
    )
    two_trial_results = Results(
        info=_make_info(num_trials=2),
        tasks=[_make_task("task-1", evaluation_criteria=EvaluationCriteria())],
        simulations=[
            _make_sim("task-1", trial=0, reward=1.0),
            _make_sim("task-1", trial=1, reward=1.0),
        ],
    )

    single_metrics = compute_metrics(single_trial_results)
    two_metrics = compute_metrics(two_trial_results)

    assert 2 not in single_metrics.pass_hat_ks
    assert two_metrics.pass_hat_ks[2] == 1.0


def test_compute_metrics_handles_tasks_without_evaluation_criteria() -> None:
    results = Results(
        info=_make_info(num_trials=1),
        tasks=[_make_task("task-1", evaluation_criteria=None)],
        simulations=[_make_sim("task-1", trial=0, reward=1.0)],
    )

    metrics = compute_metrics(results)

    assert metrics.pass_hat_ks[1] == 1.0
