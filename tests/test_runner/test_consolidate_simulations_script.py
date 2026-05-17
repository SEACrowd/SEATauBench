from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_consolidate_simulations_script_handles_json_and_dir_formats(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "simulations"

    run_a = input_dir / "run_a"
    _write_json(
        run_a / "results.json",
        {
            "timestamp": "2026-04-23T10:00:00",
            "info": {
                "experiment_name": "english_th_tools",
                "environment_info": {"domain_name": "retail"},
                "agent_info": {
                    "implementation": "llm_agent",
                    "llm": "agent-model",
                    "llm_args": {"temperature": 0.0},
                },
                "user_info": {
                    "implementation": "user_simulator",
                    "llm": "user-model",
                    "llm_args": {"temperature": 0.0},
                },
                "num_trials": 1,
                "max_steps": 200,
                "max_errors": 10,
                "seed": 300,
                "lang_id": "th",
                "lang_components": ["tools"],
                "mixed_tools_config": None,
                "auto_user_system": False,
                "retrieval_config": None,
                "retrieval_config_kwargs": None,
            },
            "tasks": [{"id": "0"}],
            "simulations": [
                {
                    "id": "sim-a",
                    "task_id": "0",
                    "trial": 0,
                    "mode": "text",
                    "termination_reason": "user_stop",
                    "reward_info": {
                        "reward": 1.0,
                        "reward_basis": ["DB"],
                        "reward_breakdown": {"DB": 1.0},
                        "db_check": {"db_match": True, "db_reward": 1.0},
                        "action_checks": [],
                        "env_assertions": [],
                        "nl_assertions": [],
                        "communicate_checks": [],
                    },
                    "messages": [
                        {"role": "assistant", "content": "Hi!"},
                        {"role": "user", "content": "Help me"},
                    ],
                    "agent_cost": 0.1,
                    "user_cost": 0.2,
                    "start_time": "2026-04-23T10:00:00",
                    "end_time": "2026-04-23T10:00:10",
                    "duration": 10.0,
                    "hallucination_retries_used": 0,
                    "hallucination_check": None,
                    "auth_classification": {"status": "succeeded"},
                    "seed": 300,
                }
            ],
        },
    )

    run_b = input_dir / "run_b"
    _write_json(
        run_b / "results.json",
        {
            "timestamp": "2026-04-23T10:05:00",
            "info": {
                "experiment_name": "english_mixed_bi",
                "environment_info": {"domain_name": "retail"},
                "agent_info": {
                    "implementation": "llm_agent",
                    "llm": "agent-model",
                    "llm_args": {"temperature": 0.0},
                },
                "user_info": {
                    "implementation": "user_simulator",
                    "llm": "user-model",
                    "llm_args": {"temperature": 0.0},
                },
                "num_trials": 1,
                "max_steps": 200,
                "max_errors": 10,
                "seed": 300,
                "lang_id": None,
                "lang_components": ["mixed_tools"],
                "mixed_tools_config": "2lang_uniform_en-th",
                "auto_user_system": False,
                "retrieval_config": None,
                "retrieval_config_kwargs": None,
            },
            "tasks": [{"id": "1"}],
            "simulation_index": [{"id": "sim-b", "task_id": "1", "trial": 0}],
            "simulations": [],
        },
    )
    _write_json(
        run_b / "simulations" / "sim-b.json",
        {
            "id": "sim-b",
            "task_id": "1",
            "trial": 0,
            "mode": "text",
            "termination_reason": "max_steps",
            "reward_info": {
                "reward": 0.0,
                "reward_basis": ["DB", "NL_ASSERTION"],
                "reward_breakdown": {"DB": 1.0, "NL_ASSERTION": 0.0},
                "db_check": {"db_match": False, "db_reward": 0.0},
                "action_checks": [{"ok": False}],
                "env_assertions": [],
                "nl_assertions": [{"ok": False}],
                "communicate_checks": [],
            },
            "messages": [
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "Need help"},
            ],
            "agent_cost": 0.3,
            "user_cost": 0.4,
            "start_time": "2026-04-23T10:05:00",
            "end_time": "2026-04-23T10:05:20",
            "duration": 20.0,
            "hallucination_retries_used": 1,
            "hallucination_check": {"status": "ok"},
            "auth_classification": {"status": "failed"},
            "seed": 301,
        },
    )

    csv_out = tmp_path / "all.csv"
    jsonl_out = tmp_path / "all.jsonl"

    subprocess.run(
        [
            sys.executable,
            "scripts/consolidate_simulations.py",
            "--input-dir",
            str(input_dir),
            "--csv-out",
            str(csv_out),
            "--jsonl-out",
            str(jsonl_out),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    with csv_out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    jsonl_rows = [
        json.loads(line) for line in jsonl_out.read_text(encoding="utf-8").splitlines()
    ]

    assert len(rows) == 2
    assert len(jsonl_rows) == 2

    first = rows[0]
    second = rows[1]

    assert first["experiment_name"] == "english_th_tools"
    assert first["lang_id"] == "th"
    assert first["reward"] == "1.0"
    assert first["first_agent_message"] == "Hi!"
    assert first["first_user_message"] == "Help me"

    assert second["experiment_name"] == "english_mixed_bi"
    assert second["mixed_tools_config"] == "2lang_uniform_en-th"
    assert second["termination_reason"] == "max_steps"
    assert second["db_match"] == "False"
    assert second["action_checks_count"] == "1"
    assert second["nl_assertions_count"] == "1"

    assert jsonl_rows[1]["run_dir_name"] == "run_b"
    assert jsonl_rows[1]["auth_status"] == "failed"
