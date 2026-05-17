from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/run_seatau.sh", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def _commands(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.startswith("$ tau2 run ")]


def test_english_tools_uses_four_default_languages() -> None:
    result = _run_script(
        "--experiment",
        "english_tools",
        "--dry-run",
        "--domain",
        "retail",
        "--agent-llm",
        "agent-model",
        "--user-llm",
        "user-model",
        "--num-trials",
        "1",
        "--num-tasks",
        "1",
    )

    commands = _commands(result.stdout)

    assert len(commands) == 4
    assert any("--lang-id th" in cmd for cmd in commands)
    assert any("--lang-id vi" in cmd for cmd in commands)
    assert any("--lang-id id" in cmd for cmd in commands)
    assert any("--lang-id zh" in cmd for cmd in commands)
    assert all("--lang-components tools" in cmd for cmd in commands)
    assert all("--no-auto-user-system" in cmd for cmd in commands)
    assert all("--experiment-name english_tools" in cmd for cmd in commands)


def test_english_mixed_tri_runs_once_with_fixed_config() -> None:
    result = _run_script(
        "--experiment",
        "english_mixed_tri",
        "--dry-run",
        "--domain",
        "retail",
        "--agent-llm",
        "agent-model",
        "--user-llm",
        "user-model",
        "--num-trials",
        "1",
        "--num-tasks",
        "1",
    )

    commands = _commands(result.stdout)

    assert commands == [
        "$ tau2 run --domain retail --agent-llm agent-model --user-llm user-model --num-trials 1 --num-tasks 1 --experiment-name english_mixed_tri --no-auto-user-system --lang-components mixed_tools --mixed-tools-config 3lang_uniform_en-th-vi"
    ]


def test_all_languages_overrides_experiment_default_language_list() -> None:
    result = _run_script(
        "--experiment",
        "english_tools",
        "--all-languages",
        "--dry-run",
        "--domain",
        "retail",
        "--agent-llm",
        "agent-model",
        "--user-llm",
        "user-model",
        "--num-trials",
        "1",
        "--num-tasks",
        "1",
    )

    commands = _commands(result.stdout)

    assert len(commands) == 5
    assert any("--lang-id tl" in cmd for cmd in commands)


def test_run_english_tool_experiments_sets_specific_experiment_names() -> None:
    result = subprocess.run(
        ["bash", "scripts/run_english_tool_experiments.sh",
         "--dry-run",
         "--domain", "retail",
         "--agent-llm", "agent-model",
         "--user-llm", "user-model",
         "--num-trials", "1",
         "--num-tasks", "1"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    commands = _commands(result.stdout)

    assert len(commands) == 8
    assert any("--experiment-name english_th_tools" in cmd for cmd in commands)
    assert any("--experiment-name english_vi_tools" in cmd for cmd in commands)
    assert any("--experiment-name english_id_tools" in cmd for cmd in commands)
    assert any("--experiment-name english_zh_tools" in cmd for cmd in commands)
    assert any("--experiment-name english_mixed_bi" in cmd for cmd in commands)
    assert any("--experiment-name english_mixed_tri" in cmd for cmd in commands)
    assert any("--experiment-name english_mixed_fourth" in cmd for cmd in commands)
    assert any("--experiment-name english_mixed_multi" in cmd for cmd in commands)
    assert any(
        "--save-to "
        "english_tool_experiments_retail_agent-model_user-model_english_th_tools" in cmd
        for cmd in commands
    )
    assert any(
        "--save-to "
        "english_tool_experiments_retail_agent-model_user-model_english_mixed_tri"
        in cmd
        for cmd in commands
    )


def test_run_english_tool_experiments_honors_save_to_prefix() -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/run_english_tool_experiments.sh",
            "--dry-run",
            "--save-to-prefix",
            "custom-prefix",
            "--domain",
            "retail",
            "--agent-llm",
            "agent-model",
            "--user-llm",
            "user-model",
            "--num-trials",
            "1",
            "--num-tasks",
            "1",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    commands = _commands(result.stdout)

    assert len(commands) == 8
    assert all("--save-to custom-prefix_" in cmd for cmd in commands)
    assert any("--save-to custom-prefix_english_zh_tools" in cmd for cmd in commands)
    assert any("--save-to custom-prefix_english_mixed_multi" in cmd for cmd in commands)


def test_run_english_tool_experiments_rejects_shared_save_to() -> None:
    result = subprocess.run(
        [
            "bash",
            "scripts/run_english_tool_experiments.sh",
            "--save-to",
            "shared-run",
            "--dry-run",
            "--domain",
            "retail",
            "--agent-llm",
            "agent-model",
            "--user-llm",
            "user-model",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "Do not pass --save-to" in result.stderr
