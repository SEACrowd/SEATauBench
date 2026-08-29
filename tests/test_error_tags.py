from __future__ import annotations

import argparse
import json
from pathlib import Path

from seatau.utils import error_tags
from tau2.scripts.review_conversation import find_results_files


def _write_reviewed(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_find_results_files_discovers_nested_simulation_runs(tmp_path: Path) -> None:
    shallow = tmp_path / "scenario_a" / "run_1" / "results.json"
    nested = tmp_path / "scenario_b" / "model" / "seed_1" / "results.json"
    reviewed = tmp_path / "scenario_b" / "model" / "seed_1" / "results_reviewed.json"
    for path in (shallow, nested, reviewed):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    assert find_results_files(tmp_path) == [shallow, nested]


def test_normalize_tags_cleans_raw_spelling_and_dedupes() -> None:
    assert error_tags.normalize_tags(
        [
            " Guideline Violation ",
            "guideleine-violation",
            "minor",
            "unknown tag",
        ],
        source="user",
    ) == ["guideline_violation", "other"]


def test_user_tags_reject_agent_only_tool_tags() -> None:
    assert error_tags.normalize_tags(
        ["tool_call_schema_error", "irrelevant_tool_call"],
        source="user",
    ) == ["other"]


def test_normalize_dry_run_does_not_write(tmp_path: Path) -> None:
    reviewed = tmp_path / "results_reviewed.json"
    payload = {
        "simulations": [
            {
                "review": {
                    "errors": [
                        {
                            "source": "agent",
                            "error_tags": [" Tool Call Argument Error "],
                        }
                    ]
                },
                "user_only_review": {
                    "errors": [
                        {
                            "error_tags": ["critical_hindered", "Wrong Sequence"],
                        }
                    ]
                },
            }
        ]
    }
    _write_reviewed(reviewed, payload)

    args = argparse.Namespace(paths=[tmp_path], dry_run=True)

    assert error_tags.cmd_normalize(args) == 0
    assert json.loads(reviewed.read_text(encoding="utf-8")) == payload


def test_normalize_rewrites_reviewed_files_by_source(tmp_path: Path) -> None:
    reviewed = tmp_path / "run" / "results_reviewed.json"
    _write_reviewed(
        reviewed,
        {
            "simulations": [
                {
                    "review": {
                        "errors": [
                            {
                                "source": "agent",
                                "error_tags": [
                                    " Tool Call Argument Error ",
                                    "mis-calculated total",
                                ],
                            },
                            {
                                "source": "user",
                                "error_tags": ["tool_call_schema_error"],
                            },
                        ]
                    },
                    "user_only_review": {
                        "errors": [
                            {
                                "error_tags": [
                                    "critical_hindered",
                                    "Wrong Sequence",
                                    "wrong_sequence",
                                ],
                            }
                        ]
                    },
                }
            ]
        },
    )

    args = argparse.Namespace(paths=[tmp_path], dry_run=False)

    assert error_tags.cmd_normalize(args) == 0
    data = json.loads(reviewed.read_text(encoding="utf-8"))
    full_errors = data["simulations"][0]["review"]["errors"]
    user_only_errors = data["simulations"][0]["user_only_review"]["errors"]
    assert full_errors[0]["error_tags"] == ["tool_call_argument_error"]
    assert full_errors[1]["error_tags"] == ["other"]
    assert user_only_errors[0]["error_tags"] == ["wrong_sequence"]
