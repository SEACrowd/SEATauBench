"""
Tests for agent metrics, specifically verifying that trial 2 results
affect performance evaluation (pass^k metrics).
"""

import pytest

from tau2.data_model.simulation import (
    AgentInfo,
    Info,
    Results,
    RewardInfo,
    SimulationRun,
    TerminationReason,
    UserInfo,
)
from tau2.data_model.tasks import make_task
from tau2.environment.environment import EnvironmentInfo
from tau2.metrics.agent_metrics import compute_metrics, pass_hat_k
from tau2.utils.utils import get_now


def make_info(num_trials: int) -> Info:
    return Info(
        git_commit="abc123",
        num_trials=num_trials,
        max_steps=100,
        max_errors=10,
        user_info=UserInfo(implementation="user_simulator", llm="gpt-4", llm_args={}),
        agent_info=AgentInfo(implementation="llm_agent", llm="gpt-4", llm_args={}),
        environment_info=EnvironmentInfo(domain_name="mock", policy="test policy"),
    )


def make_sim(task_id: str, trial: int, seed: int, reward: float) -> SimulationRun:
    return SimulationRun(
        id=f"sim_{trial}",
        task_id=task_id,
        start_time=get_now(),
        end_time=get_now(),
        duration=1.0,
        termination_reason=TerminationReason.AGENT_STOP,
        agent_cost=0.1,
        user_cost=0.1,
        reward_info=RewardInfo(reward=reward),
        messages=[],
        trial=trial,
        seed=seed,
    )


class TestPassHatK:
    """Tests for the pass_hat_k metric computation."""

    def test_pass_hat_k_single_trial_success(self):
        """With 1 trial and 1 success, pass^1 = 1.0."""
        assert pass_hat_k(num_trials=1, success_count=1, k=1) == 1.0

    def test_pass_hat_k_single_trial_failure(self):
        """With 1 trial and 0 successes, pass^1 = 0.0."""
        assert pass_hat_k(num_trials=1, success_count=0, k=1) == 0.0

    def test_pass_hat_k_two_trials_one_success(self):
        """With 2 trials and 1 success, pass^1 = 0.5."""
        assert pass_hat_k(num_trials=2, success_count=1, k=1) == 0.5

    def test_pass_hat_k_two_trials_two_successes(self):
        """With 2 trials and 2 successes, pass^1 = 1.0 and pass^2 = 1.0."""
        assert pass_hat_k(num_trials=2, success_count=2, k=1) == 1.0
        assert pass_hat_k(num_trials=2, success_count=2, k=2) == 1.0

    def test_pass_hat_k_two_trials_one_success_k2(self):
        """With 2 trials and 1 success, pass^2 = 0.0 (both trials must succeed)."""
        assert pass_hat_k(num_trials=2, success_count=1, k=2) == 0.0

    def test_pass_hat_k_invalid_k(self):
        """k cannot exceed num_trials."""
        with pytest.raises(ValueError):
            pass_hat_k(num_trials=1, success_count=1, k=2)


class TestTrial2AffectsPerformanceEvaluation:
    """
    Tests verifying that trial 2 (second trial) results affect performance evaluation.

    Trial 2 affects performance in two ways:
    1. It changes the pass^1 value (because pass^k averages over all trials)
    2. It enables computing higher-order pass^k metrics (e.g., pass^2)
    """

    def test_single_trial_metrics(self):
        """With 1 trial succeeding, pass^1 = 1.0 and no pass^2."""
        task = make_task(
            user_instructions="test task",
            eval_criteria=None,
            initialization_data=None,
            message_history=None,
        )
        results = Results(
            info=make_info(num_trials=1),
            tasks=[task],
            simulations=[make_sim(task.id, trial=0, seed=12345, reward=1.0)],
        )
        metrics = compute_metrics(results)

        assert metrics.pass_hat_ks[1] == 1.0
        assert 2 not in metrics.pass_hat_ks  # pass^2 not available with 1 trial

    def test_trial_2_changes_pass1(self):
        """
        Trial 2 changes pass^1 compared to running only 1 trial.

        With 1 trial (success): pass^1 = 1.0
        With 2 trials (1 success, 1 failure): pass^1 = 0.5

        This demonstrates that trial 2's result is included in the evaluation.
        """
        task = make_task(
            user_instructions="test task",
            eval_criteria=None,
            initialization_data=None,
            message_history=None,
        )

        # Single trial (success): pass^1 = 1.0
        results_single = Results(
            info=make_info(num_trials=1),
            tasks=[task],
            simulations=[make_sim(task.id, trial=0, seed=12345, reward=1.0)],
        )
        metrics_single = compute_metrics(results_single)

        # Two trials (trial 0: success, trial 1: failure): pass^1 = 0.5
        results_two = Results(
            info=make_info(num_trials=2),
            tasks=[task],
            simulations=[
                make_sim(task.id, trial=0, seed=12345, reward=1.0),
                make_sim(task.id, trial=1, seed=67890, reward=0.0),
            ],
        )
        metrics_two = compute_metrics(results_two)

        # Trial 2 reduces pass^1 from 1.0 to 0.5
        assert metrics_single.pass_hat_ks[1] == 1.0
        assert metrics_two.pass_hat_ks[1] == 0.5

    def test_trial_2_enables_pass2(self):
        """
        Trial 2 enables computing pass^2 (probability that both trials succeed).

        With 1 trial: pass^2 is not available.
        With 2 trials: pass^2 is computed.
        """
        task = make_task(
            user_instructions="test task",
            eval_criteria=None,
            initialization_data=None,
            message_history=None,
        )
        results = Results(
            info=make_info(num_trials=2),
            tasks=[task],
            simulations=[
                make_sim(task.id, trial=0, seed=12345, reward=1.0),
                make_sim(task.id, trial=1, seed=67890, reward=1.0),
            ],
        )
        metrics = compute_metrics(results)

        assert 2 in metrics.pass_hat_ks  # pass^2 is available
        assert metrics.pass_hat_ks[1] == 1.0
        assert metrics.pass_hat_ks[2] == 1.0

    def test_both_trials_must_succeed_for_pass2(self):
        """
        pass^2 = 1.0 only if BOTH trials succeed.
        If trial 2 fails, pass^2 = 0.0.
        """
        task = make_task(
            user_instructions="test task",
            eval_criteria=None,
            initialization_data=None,
            message_history=None,
        )
        results = Results(
            info=make_info(num_trials=2),
            tasks=[task],
            simulations=[
                make_sim(task.id, trial=0, seed=12345, reward=1.0),  # success
                make_sim(task.id, trial=1, seed=67890, reward=0.0),  # failure
            ],
        )
        metrics = compute_metrics(results)

        assert metrics.pass_hat_ks[1] == 0.5  # half succeed
        assert metrics.pass_hat_ks[2] == 0.0  # both don't succeed

    def test_task_without_eval_criteria(self):
        """
        Tasks without evaluation criteria should not cause errors during metrics computation.
        This tests the fix for the KeyError when evaluation_criteria is None.
        """
        task = make_task(
            user_instructions="test task",
            eval_criteria=None,
            initialization_data=None,
            message_history=None,
        )
        assert task.evaluation_criteria is None

        results = Results(
            info=make_info(num_trials=2),
            tasks=[task],
            simulations=[
                make_sim(task.id, trial=0, seed=12345, reward=1.0),
                make_sim(task.id, trial=1, seed=67890, reward=0.0),
            ],
        )
        # Should not raise KeyError
        metrics = compute_metrics(results)
        assert metrics.pass_hat_ks[1] == 0.5
        assert metrics.pass_hat_ks[2] == 0.0
