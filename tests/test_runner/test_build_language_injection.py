from types import SimpleNamespace

import pytest

from tau2.data_model.simulation import TextRunConfig
from tau2.environment.environment import Environment
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool
from tau2.registry import registry
from tau2.runner.build import apply_language_config, build_user
from translation.language import LanguageConfig


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


def test_build_user_injects_user_prompt_only_when_user_system_enabled(monkeypatch):
    monkeypatch.setattr(registry, "get_user_constructor", lambda _: _CaptureUser)
    monkeypatch.setattr(
        "tau2.runner.build.get_language_config",
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
        "tau2.runner.build.get_language_config",
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
        "tau2.runner.build.get_language_config",
        lambda *_: pytest.fail("languages.json should not be loaded in this case"),
    )

    config = TextRunConfig(domain="mock", lang_id="vi", lang_components=["db"])
    env = Environment(domain_name="mock", policy="POLICY")

    assert apply_language_config(env, config) is None
    assert env.get_policy() == "POLICY"


def test_apply_language_config_appends_agent_system_prompt(monkeypatch):
    monkeypatch.setattr(
        "tau2.runner.build.get_language_config",
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
        "tau2.runner.build.get_language_config",
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

    monkeypatch.setattr("tau2.runner.build.DATA_DIR", data_dir)
    monkeypatch.setattr(
        "translation.runtime_localization.apply_schema_runtime_localization",
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
