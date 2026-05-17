from __future__ import annotations

import csv
from pathlib import Path

from tau2.data_model.simulation import (
    ActionCheck,
    AgentInfo,
    DBCheck,
    Info,
    Results,
    RewardInfo,
    SimulationRun,
    UserInfo,
)
from tau2.data_model.tasks import Action, Task
from tau2.environment.environment import EnvironmentInfo
from tau2.environment.toolkit import ToolType
from tau2.scripts.summarize_results import (
    COLUMNS,
    build_summary_rows,
    write_summary_csv,
)


def _task(task_id: str) -> Task:
    return Task(
        id=task_id,
        user_scenario={"instructions": "Complete the test task."},
    )


def _action_check(name: str, matched: bool, tool_type: ToolType) -> ActionCheck:
    return ActionCheck(
        action=Action(action_id=name, name=name, arguments={}),
        action_match=matched,
        action_reward=1.0 if matched else 0.0,
        tool_type=tool_type,
    )


def _simulation(
    *,
    sim_id: str,
    task_id: str,
    trial: int,
    reward: float,
    db_match: bool,
    action_checks: list[ActionCheck],
    termination_reason: str,
    review: dict | None = None,
) -> SimulationRun:
    return SimulationRun(
        id=sim_id,
        task_id=task_id,
        trial=trial,
        start_time="2026-04-23T10:00:00",
        end_time="2026-04-23T10:00:10",
        duration=10.0,
        termination_reason=termination_reason,
        agent_cost=0.1 + trial * 0.2,
        user_cost=0.0,
        reward_info=RewardInfo(
            reward=reward,
            db_check=DBCheck(db_match=db_match, db_reward=reward),
            action_checks=action_checks,
        ),
        review=review,
    )


def _results(experiment_name: str, simulations: list[SimulationRun]) -> Results:
    return Results(
        info=Info(
            git_commit="abc123",
            experiment_name=experiment_name,
            num_trials=2,
            max_steps=200,
            max_errors=10,
            user_info=UserInfo(implementation="user_simulator", llm="user-model"),
            agent_info=AgentInfo(implementation="llm_agent", llm="agent-model"),
            environment_info=EnvironmentInfo(domain_name="retail", policy="policy"),
        ),
        tasks=[_task("0")],
        simulations=simulations,
    )


def test_build_summary_rows_outputs_requested_columns(tmp_path: Path) -> None:
    run_dir = tmp_path / "simulations" / "english_tool_experiments_retail_agent-user_english_mixed_bi"
    results = _results(
        "english_mixed_bi",
        [
            _simulation(
                sim_id="sim-1",
                task_id="0",
                trial=0,
                reward=1.0,
                db_match=True,
                action_checks=[
                    _action_check("read_order", True, ToolType.READ),
                    _action_check("update_order", False, ToolType.WRITE),
                ],
                termination_reason="user_stop",
                review={
                    "has_errors": True,
                    "agent_error": True,
                    "user_error": True,
                    "errors": [
                        {
                            "source": "agent",
                            "severity": "critical",
                            "error_tags": ["missed_required_action"],
                            "reasoning": "Agent missed a required action.",
                        },
                        {
                            "source": "user",
                            "severity": "minor",
                            "error_tags": ["inconsistent_behavior"],
                            "reasoning": "User was mildly inconsistent.",
                        },
                    ],
                },
            ),
            _simulation(
                sim_id="sim-2",
                task_id="0",
                trial=1,
                reward=0.0,
                db_match=False,
                action_checks=[_action_check("read_order", False, ToolType.READ)],
                termination_reason="agent_stop",
                review={"has_errors": False, "errors": []},
            ),
        ],
    )
    results.save(run_dir / "results.json")

    rows = build_summary_rows(tmp_path / "simulations")

    assert len(rows) == 1
    row = rows[0]
    assert list(row) == COLUMNS
    assert row["experiment"] == "mixed_bi"
    assert (
        row["full_experiment_name"]
        == "english_tool_experiments_retail_agent-user_english_mixed_bi"
    )
    assert row["domain"] == "retail"
    assert row["agent_model"] == "agent-model"
    assert row["user_model"] == "user-model"
    assert row["pass_1"] == 0.5
    assert row["pass_2"] == 0.0
    assert row["pass_3"] == ""
    assert row["total_simulations"] == 2
    assert row["total_tasks"] == 1
    assert row["average_reward"] == 0.5
    assert row["avg_cost_per_conversation"] == 0.2
    assert row["read_actions_count"] == 1
    assert row["read_actions_total"] == 2
    assert row["read_actions_percent"] == 50.0
    assert row["write_actions_count"] == 0
    assert row["write_actions_total"] == 1
    assert row["write_actions_percent"] == 0.0
    assert row["db_match_count"] == 1
    assert row["db_mismatch_count"] == 1
    assert row["db_match_percent"] == 50.0
    assert row["authentication_not_checked"] == 2
    assert row["normal_stop_total"] == 2
    assert row["normal_stop_user"] == 1
    assert row["normal_stop_agent"] == 1
    assert row["agent_errors"] == 1
    assert row["agent_error_sims_by_severity"] == "critical=1"
    assert row["user_errors"] == 1
    assert row["user_error_sims_by_severity"] == "minor=1"

    csv_path = tmp_path / "summary.csv"
    write_summary_csv(csv_path, rows)
    with csv_path.open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))

    assert csv_rows[0]["experiment"] == "mixed_bi"
    assert (
        csv_rows[0]["full_experiment_name"]
        == "english_tool_experiments_retail_agent-user_english_mixed_bi"
    )
    assert csv_rows[0]["domain"] == "retail"
    assert csv_rows[0]["agent_model"] == "agent-model"
    assert csv_rows[0]["user_model"] == "user-model"
    assert csv_rows[0]["agent_error_sims_by_severity"] == "critical=1"


def test_reviewed_file_wins_even_next_to_simulations_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "simulations" / "run_a"
    original = _results(
        "english_original",
        [
            _simulation(
                sim_id="sim-1",
                task_id="0",
                trial=0,
                reward=0.0,
                db_match=False,
                action_checks=[],
                termination_reason="user_stop",
            )
        ],
    )
    reviewed = _results(
        "english_reviewed",
        [
            _simulation(
                sim_id="sim-1",
                task_id="0",
                trial=0,
                reward=1.0,
                db_match=True,
                action_checks=[],
                termination_reason="user_stop",
            )
        ],
    )

    original.save(run_dir / "results.json", format="dir")
    reviewed.save(run_dir / "results_reviewed.json")

    rows = build_summary_rows(tmp_path / "simulations")

    assert len(rows) == 1
    assert rows[0]["experiment"] == "reviewed"
    assert rows[0]["average_reward"] == 1.0
