from __future__ import annotations

import shlex

import pytest

from seatau.cli import main


def _commands(capsys: pytest.CaptureFixture[str]) -> list[list[str]]:
    out = capsys.readouterr().out
    return [shlex.split(line[2:]) for line in out.splitlines() if line.startswith("$ ")]


def _run(*args: str) -> None:
    exit_code = main(["--dry-run", *args])
    assert exit_code == 0


def _assert_common_prefix(command: list[str]) -> None:
    assert command[:4] == ["uv", "run", "tau2", "run"]
    assert command[4:6] == ["--domain", "retail"]
    assert command[6:8] == ["--agent-llm", "azure/kimi-k2.5"]


def test_baseline_without_lang_id(capsys: pytest.CaptureFixture[str]) -> None:
    _run("--experiment", "baseline", "--domain", "retail", "--agent-llm", "azure/kimi-k2.5")
    assert _commands(capsys) == [
        ["uv", "run", "tau2", "run", "--domain", "retail", "--agent-llm", "azure/kimi-k2.5"]
    ]


def test_crosslingual_fans_out_over_languages(capsys: pytest.CaptureFixture[str]) -> None:
    _run("--experiment", "crosslingual", "--domain", "retail", "--agent-llm", "azure/kimi-k2.5")
    commands = _commands(capsys)
    expected_langs = ["id", "th", "tl", "vi", "zh"]
    assert [command[9] for command in commands] == expected_langs
    for command, lang in zip(commands, expected_langs, strict=True):
        _assert_common_prefix(command)
        assert command[8:12] == ["--lang-id", lang, "--seatau-experiment", "crosslingual"]


def test_mixed_tools_uses_mixed_config(capsys: pytest.CaptureFixture[str]) -> None:
    _run("--experiment", "mixed_tools", "--domain", "retail", "--agent-llm", "azure/kimi-k2.5")
    out = capsys.readouterr().out
    assert (
        "[SKIP] mixed_tools for lang 'tl': no default config available." in out
    )
    commands = [shlex.split(line[2:]) for line in out.splitlines() if line.startswith("$ ")]
    expected = [
        ("id", "5lang_uniform_en-th-vi-id-zh"),
        ("th", "2lang_uniform_en-th"),
        ("vi", "5lang_uniform_en-th-vi-id-zh"),
        ("zh", "5lang_uniform_en-th-vi-id-zh"),
    ]
    assert [command[9] for command in commands] == [lang for lang, _ in expected]
    for command, (lang, config_name) in zip(commands, expected, strict=True):
        _assert_common_prefix(command)
        assert command[8:14] == [
            "--lang-id",
            lang,
            "--seatau-experiment",
            "mixed_tools",
            "--mixed-tools-config",
            config_name,
        ]


def test_translated_fans_out_over_languages(capsys: pytest.CaptureFixture[str]) -> None:
    _run("--experiment", "translated", "--domain", "retail", "--agent-llm", "azure/kimi-k2.5")
    commands = _commands(capsys)
    expected_langs = ["id", "th", "tl", "vi", "zh"]
    assert [command[9] for command in commands] == expected_langs
    for command, lang in zip(commands, expected_langs, strict=True):
        _assert_common_prefix(command)
        assert command[8:12] == ["--lang-id", lang, "--seatau-experiment", "translated"]


def test_mock_domain_skips_with_exit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--dry-run", "--experiment", "baseline", "--domain", "mock"])
    assert exc.value.code == 0
    assert "[SKIP]" in capsys.readouterr().out


def test_unknown_experiment_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--dry-run", "--experiment", "bogus", "--domain", "retail"])
    assert exc.value.code == 2
    assert "Unknown experiment" in capsys.readouterr().err


def test_unknown_domain_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--dry-run", "--experiment", "baseline", "--domain", "bogus"])
    assert exc.value.code == 2
    assert "Unknown domain" in capsys.readouterr().err


def test_unknown_lang_id_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "--dry-run",
                "--experiment",
                "crosslingual",
                "--domain",
                "retail",
                "--lang-id",
                "xx",
            ]
        )
    assert exc.value.code == 2
    assert "Unknown lang-id" in capsys.readouterr().err


def test_mutually_exclusive_experiment_flags() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--dry-run", "--experiment", "baseline", "--all-experiments"])
    assert exc.value.code == 2


def test_alias_resolves_to_mixed_tools(capsys: pytest.CaptureFixture[str]) -> None:
    _run("--experiment", "trans_tool", "--domain", "retail", "--agent-llm", "azure/kimi-k2.5")
    out = capsys.readouterr().out
    assert "--seatau-experiment mixed_tools" in out
