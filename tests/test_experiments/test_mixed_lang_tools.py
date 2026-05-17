from pathlib import Path

from experiments.mixed_lang_tools.diagnostics import diagnose_mixed_tools_configs
from experiments.mixed_lang_tools.partition import (
    extract_function_docstrings,
    load_mixed_tools_config,
    partition_tools_by_language,
)


def test_extract_function_docstrings_only_includes_decorated_tools(
    tmp_path: Path,
) -> None:
    tools_file = tmp_path / "tools.py"
    tools_file.write_text(
        "from tau2.environment.toolkit import ToolType, is_discoverable_tool, is_tool\n"
        "\n"
        "class DemoTools:\n"
        '    """Demo tools."""\n'
        "\n"
        "    @is_tool(ToolType.READ)\n"
        "    def ping(self):\n"
        '        """Ping the service."""\n'
        "        ...\n"
        "\n"
        "    def helper(self):\n"
        '        """Internal helper."""\n'
        "        ...\n"
        "\n"
        "    @is_discoverable_tool(ToolType.WRITE)\n"
        "    async def unlock(self):\n"
        '        """Unlock a hidden tool."""\n'
        "        ...\n"
        "\n"
        "    def assert_state(self):\n"
        '        """Assertion helper."""\n'
        "        ...\n",
        encoding="utf-8",
    )

    docstrings = extract_function_docstrings(tools_file)

    assert docstrings["ping"] == "Ping the service."
    assert docstrings["unlock"] == "Unlock a hidden tool."
    assert "helper" not in docstrings
    assert "assert_state" not in docstrings


def test_load_four_language_mixed_tools_config() -> None:
    config = load_mixed_tools_config("4lang_uniform_en-th-vi-id")

    assert config.languages.codes == ["en", "th", "vi", "id"]
    assert config.languages.weights == [0.25, 0.25, 0.25, 0.25]
    assert config.partitioning.partition_strategy == "nested_progressive"
    assert config.partitioning.tools_per_added_language == 3
    assert config.partitioning.group_mode is False


def test_telecom_mixed_tools_diagnostics_show_full_docstring_coverage() -> None:
    diagnostics = diagnose_mixed_tools_configs(
        domain="telecom",
        config_names=[
            "2lang_uniform_en-th",
            "3lang_uniform_en-th-vi",
            "4lang_uniform_en-th-vi-id",
            "5lang_uniform_en-th-vi-id-zh",
        ],
    )

    assert [item["config_name"] for item in diagnostics["configs"]] == [
        "2lang_uniform_en-th",
        "3lang_uniform_en-th-vi",
        "4lang_uniform_en-th-vi-id",
        "5lang_uniform_en-th-vi-id-zh",
    ]
    assert all(
        item["docstring_count"] == item["tool_count"] for item in diagnostics["configs"]
    )
    assert all(item["missing_docstrings"] == [] for item in diagnostics["configs"])


def test_telecom_default_mixed_tools_configs_are_nested_progressive() -> None:
    diagnostics = diagnose_mixed_tools_configs(
        domain="telecom",
        config_names=[
            "2lang_uniform_en-th",
            "3lang_uniform_en-th-vi",
            "4lang_uniform_en-th-vi-id",
            "5lang_uniform_en-th-vi-id-zh",
        ],
    )

    assert all(
        item["partition_strategy"] == "nested_progressive"
        for item in diagnostics["configs"]
    )
    assert all(
        comparison["is_nested_progressive"] for comparison in diagnostics["comparisons"]
    )
    assert all(
        comparison["previous_non_english_changed"] == {}
        for comparison in diagnostics["comparisons"]
    )
    english_counts = [
        item["summary"]["by_language"].get("en", 0) for item in diagnostics["configs"]
    ]
    assert english_counts == [10, 7, 4, 1]

    for item in diagnostics["configs"]:
        for lang in item["languages"][1:]:
            assert item["summary"]["by_language"][lang] == 3


def test_nested_progressive_partition_is_domain_agnostic_with_groups() -> None:
    tools = ["lookup", "pay", "refund", "status", "transfer"]
    groups = {"billing": ["pay", "refund"]}

    bi_assignments, bi_groups = partition_tools_by_language(
        tools,
        ["en", "th"],
        [0.5, 0.5],
        seed=7,
        tool_groups=groups,
        partition_strategy="nested_progressive",
        tools_per_added_language=1,
    )
    tri_assignments, tri_groups = partition_tools_by_language(
        tools,
        ["en", "th", "vi"],
        [0.34, 0.33, 0.33],
        seed=7,
        tool_groups=groups,
        partition_strategy="nested_progressive",
        tools_per_added_language=1,
    )

    assert bi_assignments["pay"].lang == bi_assignments["refund"].lang
    assert tri_assignments["pay"].lang == tri_assignments["refund"].lang
    assert bi_groups is not None
    assert tri_groups is not None
    assert bi_groups["billing"] == bi_assignments["pay"].lang
    assert tri_groups["billing"] == tri_assignments["pay"].lang

    for tool, assignment in bi_assignments.items():
        if assignment.lang != "en":
            assert tri_assignments[tool].lang == assignment.lang
