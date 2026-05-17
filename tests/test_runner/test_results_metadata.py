from tau2.data_model.persona import PersonaConfig
from tau2.data_model.simulation import TextRunConfig
from tau2.environment.environment import EnvironmentInfo
from tau2.runner.helpers import get_info, make_run_name


def test_get_info_includes_experiment_and_language_metadata(monkeypatch) -> None:
    monkeypatch.setattr("tau2.runner.helpers.get_commit_hash", lambda: "abc123")
    monkeypatch.setattr(
        "tau2.runner.helpers.get_environment_info",
        lambda *args, **kwargs: EnvironmentInfo(
            domain_name="retail",
            policy="policy",
        ),
    )

    config = TextRunConfig(
        domain="retail",
        agent="llm_agent",
        user="user_simulator",
        llm_agent="agent-model",
        llm_user="user-model",
        lang_id="th",
        lang_components=["tools"],
        mixed_tools_config="2lang_uniform_en-th",
        experiment_name="english_th_tools",
        auto_user_system=False,
    )

    info = get_info(
        config,
        user_persona_config=PersonaConfig(),
    )

    assert info.git_commit == "abc123"
    assert info.experiment_name == "english_th_tools"
    assert info.lang_id == "th"
    assert info.lang_components == ["tools"]
    assert info.mixed_tools_config == "2lang_uniform_en-th"
    assert info.auto_user_system is False


def test_make_run_name_appends_sanitized_experiment_name(monkeypatch) -> None:
    monkeypatch.setattr(
        "tau2.runner.helpers.get_now",
        lambda use_compact_format=True: "20260423_101612",
    )

    config = TextRunConfig(
        domain="retail",
        agent="llm_agent",
        user="user_simulator",
        llm_agent="vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas",
        llm_user="vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas",
        experiment_name="english_th_tools",
    )

    assert make_run_name(config) == (
        "20260423_101612_retail_"
        "llm_agent_qwen3-235b-a22b-instruct-2507-maas_"
        "user_simulator_qwen3-235b-a22b-instruct-2507-maas_"
        "english_th_tools"
    )


def test_make_run_name_sanitizes_experiment_name_for_paths(monkeypatch) -> None:
    monkeypatch.setattr(
        "tau2.runner.helpers.get_now",
        lambda use_compact_format=True: "20260423_101612",
    )

    config = TextRunConfig(
        domain="retail",
        agent="llm_agent",
        user="user_simulator",
        llm_agent="agent-model",
        llm_user="user-model",
        experiment_name="english/th tools",
    )

    assert make_run_name(config).endswith("_english_th_tools")
