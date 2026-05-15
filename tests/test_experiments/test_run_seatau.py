from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_SEATAU_SCRIPT = REPO_ROOT / "scripts" / "run_seatau.sh"


def _run_seatau_dry_run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(RUN_SEATAU_SCRIPT), "--dry-run", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_commands(stdout: str) -> list[list[str]]:
    return [
        shlex.split(line[2:]) for line in stdout.splitlines() if line.startswith("$ ")
    ]


def _assert_common_prefix(command: list[str]) -> None:
    assert command[:4] == ["uv", "run", "tau2", "run"]
    assert command[4:6] == ["--domain", "retail"]
    assert command[6:8] == ["--agent-llm", "azure/kimi-k2.5"]


def test_run_seatau_baseline_without_lang_id() -> None:
    result = _run_seatau_dry_run(
        "--experiment",
        "baseline",
        "--domain",
        "retail",
        "--agent-llm",
        "azure/kimi-k2.5",
    )

    commands = _run_commands(result.stdout)

    assert commands == [
        [
            "uv",
            "run",
            "tau2",
            "run",
            "--domain",
            "retail",
            "--agent-llm",
            "azure/kimi-k2.5",
        ]
    ]


def test_run_seatau_crosslingual_fans_out_over_languages() -> None:
    result = _run_seatau_dry_run(
        "--experiment",
        "crosslingual",
        "--domain",
        "retail",
        "--agent-llm",
        "azure/kimi-k2.5",
    )

    commands = _run_commands(result.stdout)
    expected_langs = ["id", "th", "tl", "vi", "zh"]

    assert [command[9] for command in commands] == expected_langs
    for command, lang in zip(commands, expected_langs, strict=True):
        assert command == [
            "uv",
            "run",
            "tau2",
            "run",
            "--domain",
            "retail",
            "--agent-llm",
            "azure/kimi-k2.5",
            "--lang-id",
            lang,
            "--seatau-experiment",
            "crosslingual",
            "--seatau-target-lang",
            lang,
            "--seatau-asset-mode",
            "original",
            "--lang-components",
            "user_system",
            "agent_system",
            "greeting",
        ]
        _assert_common_prefix(command)


def test_run_seatau_mixed_tools_uses_mixed_config() -> None:
    result = _run_seatau_dry_run(
        "--experiment",
        "mixed_tools",
        "--domain",
        "retail",
        "--agent-llm",
        "azure/kimi-k2.5",
    )

    commands = _run_commands(result.stdout)
    expected = [
        (
            "id",
            "5lang_uniform_en-th-vi-id-zh",
        ),
        (
            "th",
            "2lang_uniform_en-th",
        ),
        (
            "vi",
            "5lang_uniform_en-th-vi-id-zh",
        ),
        (
            "zh",
            "5lang_uniform_en-th-vi-id-zh",
        ),
    ]

    assert (
        "[SKIP] mixed_tools for lang 'tl': no default config available."
        in result.stdout
    )
    assert [command[13] for command in commands] == [lang for lang, _ in expected]

    for command, (lang, config_name) in zip(commands, expected, strict=True):
        assert command == [
            "uv",
            "run",
            "tau2",
            "run",
            "--domain",
            "retail",
            "--agent-llm",
            "azure/kimi-k2.5",
            "--lang-id",
            "en",
            "--seatau-experiment",
            "mixed_tools",
            "--seatau-target-lang",
            lang,
            "--seatau-asset-mode",
            "original",
            "--lang-components",
            "mixed_tools",
            "--mixed-tools-config",
            config_name,
        ]
        _assert_common_prefix(command)


def test_run_seatau_translated_fans_out_over_languages() -> None:
    result = _run_seatau_dry_run(
        "--experiment",
        "translated",
        "--domain",
        "retail",
        "--agent-llm",
        "azure/kimi-k2.5",
    )

    commands = _run_commands(result.stdout)
    expected_langs = ["id", "th", "tl", "vi", "zh"]

    assert [command[9] for command in commands] == expected_langs
    for command, lang in zip(commands, expected_langs, strict=True):
        assert command == [
            "uv",
            "run",
            "tau2",
            "run",
            "--domain",
            "retail",
            "--agent-llm",
            "azure/kimi-k2.5",
            "--lang-id",
            lang,
            "--seatau-experiment",
            "translated",
            "--seatau-target-lang",
            lang,
            "--seatau-asset-mode",
            "translated",
            "--lang-components",
            "user_system",
            "agent_system",
            "greeting",
            "tools",
            "policy",
            "db",
            "tasks",
        ]
        _assert_common_prefix(command)
