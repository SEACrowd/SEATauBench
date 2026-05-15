from pathlib import Path

from seatau.mixed_lang_tools.partition import extract_function_docstrings


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
