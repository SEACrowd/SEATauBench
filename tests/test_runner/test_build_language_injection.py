from types import SimpleNamespace

import pytest

from seatau.translation.language import LanguageConfig
from tau2.data_model.simulation import TextRunConfig
from tau2.environment.environment import Environment
from tau2.environment.toolkit import (
    ToolKitBase,
    ToolType,
    is_discoverable_tool,
    is_tool,
)
from tau2.registry import registry
from tau2.runner.build import apply_language_config, build_user


class _CaptureUser:
    def __init__(self, **kwargs):
        self.instructions = kwargs["instructions"]


def _task(user_scenario: str):
    return SimpleNamespace(user_scenario=user_scenario, user_tools=None)


class _ToolKit(ToolKitBase):
    @is_tool(ToolType.READ)
    def ping(self) -> str:
        """
        Ping.

        Returns:
            pong
        """
        return "pong"


class _MixedToolKit(ToolKitBase):
    @is_tool(ToolType.READ)
    def ping(self) -> str:
        """
        Ping.

        Returns:
            pong
        """
        return "pong"

    @is_discoverable_tool(ToolType.READ)
    def hidden(self) -> str:
        """
        Hidden.

        Returns:
            hidden
        """
        return "hidden"

    def helper(self) -> str:
        return "helper"


def test_build_user_injects_user_prompt_only_when_user_system_enabled(monkeypatch):
    monkeypatch.setattr(registry, "get_user_constructor", lambda _: _CaptureUser)
    monkeypatch.setattr(
        "tau2.runner.language.get_language_config",
        lambda _: LanguageConfig(
            code="xx",
            display_name="X",
            instruction_label="X",
            greeting="HELLO",
            user_instruction="USER_SYSTEM_PROMPT",
            agent_instruction="AGENT_SYSTEM_PROMPT",
        ),
    )

    env = Environment(domain_name="mock", policy="policy")

    user_with_system = build_user(
        "user_simulator",
        env,
        _task("SCENARIO"),
        lang_id="xx",
        lang_components={"user_system"},
    )
    user_without_system = build_user(
        "user_simulator",
        env,
        _task("SCENARIO"),
        lang_id="xx",
        lang_components={"agent_system"},
    )

    assert user_with_system.instructions.startswith("USER_SYSTEM_PROMPT\n\nSCENARIO")
    assert user_without_system.instructions == "SCENARIO"


def test_build_user_uses_default_user_prompt_when_not_overridden(monkeypatch):
    monkeypatch.setattr(registry, "get_user_constructor", lambda _: _CaptureUser)
    monkeypatch.setattr(
        "tau2.runner.language.get_language_config",
        lambda _: LanguageConfig(
            code="xx",
            display_name="Thai",
            instruction_label="Thai (ภาษาไทย)",
            greeting="HELLO",
        ),
    )

    env = Environment(domain_name="mock", policy="policy")

    user = build_user(
        "user_simulator",
        env,
        _task("SCENARIO"),
        lang_id="xx",
        lang_components={"user_system"},
    )

    assert "You must converse with the agent entirely in Thai (ภาษาไทย)." in (
        user.instructions
    )
    assert "tool names, tool argument names" in user.instructions


def test_apply_language_config_skips_languages_json_when_agent_greeting_disabled(
    monkeypatch,
):
    monkeypatch.setattr(
        "tau2.runner.language.get_language_config",
        lambda *_: pytest.fail("languages.json should not be loaded in this case"),
    )

    config = TextRunConfig(domain="mock", lang_id="vi", lang_components=["db"])
    env = Environment(domain_name="mock", policy="POLICY")

    assert apply_language_config(env, config) is None
    assert env.get_policy() == "POLICY"


def test_apply_language_config_appends_agent_system_prompt(monkeypatch):
    monkeypatch.setattr(
        "tau2.runner.language.get_language_config",
        lambda _: LanguageConfig(
            code="xx",
            display_name="X",
            instruction_label="X",
            greeting="HELLO",
            user_instruction="USER_SYSTEM_PROMPT",
            agent_instruction="AGENT_SYSTEM_PROMPT",
        ),
    )

    config = TextRunConfig(
        domain="mock", lang_id="vi", lang_components=["agent_system"]
    )
    env = Environment(domain_name="mock", policy="POLICY")

    apply_language_config(env, config)

    assert env.get_policy().endswith("AGENT_SYSTEM_PROMPT")


def test_apply_language_config_uses_default_agent_prompt_when_not_overridden(
    monkeypatch,
):
    monkeypatch.setattr(
        "tau2.runner.language.get_language_config",
        lambda _: LanguageConfig(
            code="xx",
            display_name="Thai",
            instruction_label="Thai (ภาษาไทย)",
            greeting="HELLO",
        ),
    )

    config = TextRunConfig(
        domain="mock", lang_id="vi", lang_components=["agent_system"]
    )
    env = Environment(domain_name="mock", policy="POLICY")

    apply_language_config(env, config)

    assert env.get_policy().endswith(
        "If the user writes in Thai, you must reply in Thai."
    )


def test_apply_language_config_attaches_schema_runtime_localizer(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    translated_root = data_dir / "tau2" / "domains" / "mock" / "vi"
    translated_root.mkdir(parents=True)
    (translated_root / "data_model.json").write_text("{}", encoding="utf-8")

    calls = []

    monkeypatch.setattr("tau2.runner.language.DATA_DIR", data_dir)
    monkeypatch.setattr(
        "seatau.translation.runtime_localization.apply_schema_runtime_localization",
        lambda environment, **kwargs: calls.append((environment, kwargs)),
    )

    config = TextRunConfig(domain="mock", lang_id="vi", lang_components=["tools", "db"])
    env = Environment(domain_name="mock", policy="POLICY", tools=_ToolKit())

    apply_language_config(env, config)

    assert len(calls) == 1
    patched_env, kwargs = calls[0]
    assert patched_env is env
    assert kwargs["domain"] == "mock"
    assert kwargs["translated_root"] == translated_root
    assert kwargs["localize_tools"] is True
    assert kwargs["localize_outputs"] is True


def test_apply_language_config_mixed_tools_uses_only_agent_visible_tools(
    monkeypatch,
):
    captured: dict[str, object] = {}

    def fake_load_mixed_docstrings(domain, tool_names, config, src_tools_path):
        captured["domain"] = domain
        captured["tool_names"] = tool_names
        captured["src_tools_path"] = src_tools_path
        partition = SimpleNamespace(
            summary=SimpleNamespace(by_language={"en": len(tool_names)}),
            group_assignments=None,
        )
        return {}, partition

    monkeypatch.setattr(
        "seatau.mixed_lang_tools.load_mixed_tools_config",
        lambda _: object(),
    )
    monkeypatch.setattr(
        "seatau.mixed_lang_tools.load_mixed_docstrings",
        fake_load_mixed_docstrings,
    )
    monkeypatch.setattr(
        "seatau.translation.loader.patch_toolkit_docstrings",
        lambda *args, **kwargs: {},
    )

    config = TextRunConfig(
        domain="mock",
        lang_id="vi",
        lang_components=["mixed_tools"],
        mixed_tools_config="dummy",
    )
    env = Environment(domain_name="mock", policy="POLICY", tools=_MixedToolKit())

    apply_language_config(env, config)

    assert captured["domain"] == "mock"
    assert captured["tool_names"] == ["ping"]
