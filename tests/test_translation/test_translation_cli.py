from __future__ import annotations

from click.testing import CliRunner

from translation.cli import cli
from translation.config import DEFAULT_VERTEX_MODEL


def test_help_mentions_required_vertex_model() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert DEFAULT_VERTEX_MODEL in result.output


def test_help_exposes_concurrency_without_rpm_or_proxy_options() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--max-concurrency" in result.output
    assert "--max-rpm" not in result.output
    assert "--api-key-env" not in result.output
    assert "--api-base" not in result.output
    assert "--api-version" not in result.output
