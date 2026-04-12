from types import SimpleNamespace

import pytest

from tau2.data_model.simulation import TextRunConfig
from tau2.environment.environment import Environment
from tau2.runner.build import apply_language_config, build_user
from tau2.registry import registry
from translation.language import LanguageConfig


class _CaptureUser:
    def __init__(self, **kwargs):
        self.instructions = kwargs["instructions"]


def _task(user_scenario: str):
    return SimpleNamespace(user_scenario=user_scenario, user_tools=None)


def test_build_user_injects_user_prompt_only_when_user_system_enabled(monkeypatch):
    monkeypatch.setattr(registry, "get_user_constructor", lambda _: _CaptureUser)
    monkeypatch.setattr(
        "translation.language.get_language_config",
        lambda _: LanguageConfig(
            code="xx",
            display_name="X",
            instruction_label="X",
            user_instruction="USER_SYSTEM_PROMPT",
            agent_instruction="AGENT_SYSTEM_PROMPT",
            greeting="HELLO",
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


def test_apply_language_config_skips_languages_json_when_agent_greeting_disabled(
    monkeypatch,
):
    monkeypatch.setattr(
        "translation.language.get_language_config",
        lambda *_: pytest.fail("languages.json should not be loaded in this case"),
    )

    config = TextRunConfig(domain="mock", lang_id="vi", lang_components=["db"])
    env = Environment(domain_name="mock", policy="POLICY")

    assert apply_language_config(env, config) is None
    assert env.get_policy() == "POLICY"


def test_apply_language_config_appends_agent_system_prompt(monkeypatch):
    monkeypatch.setattr(
        "translation.language.get_language_config",
        lambda _: LanguageConfig(
            code="xx",
            display_name="X",
            instruction_label="X",
            user_instruction="USER_SYSTEM_PROMPT",
            agent_instruction="AGENT_SYSTEM_PROMPT",
            greeting="HELLO",
        ),
    )

    config = TextRunConfig(domain="mock", lang_id="vi", lang_components=["agent_system"])
    env = Environment(domain_name="mock", policy="POLICY")

    apply_language_config(env, config)

    assert env.get_policy().endswith("AGENT_SYSTEM_PROMPT")
