"""SEA-TAU run metadata logging helpers."""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from seatau.experiment_matrix import get_experiment_preset


@dataclass(frozen=True)
class SeatauRunSettings:
    """Resolved SEA-TAU metadata for one tau2 run invocation."""

    experiment: str
    target_lang: str
    run_lang_id: str
    asset_mode: str
    lang_components: tuple[str, ...]
    mixed_tools_config: str | None
    user_conversation: str
    agent_conversation: str
    greeting: str
    tools: str
    context: str


def build_seatau_run_settings(
    experiment: str,
    lang_id: str,
    mixed_tools_config: str | None = None,
) -> SeatauRunSettings:
    """Resolve SEA-TAU display metadata for one run."""
    preset = get_experiment_preset(experiment)
    target_lang = lang_id
    run_lang_id = "en" if preset.mixed_tools else target_lang
    components = preset.lang_components

    user_conv = "English"
    agent_conv = "English"
    greeting_lang = "English"
    tool_lang = "English"
    context_lang = "English"

    if preset.mixed_tools:
        tool_lang = f"Mixed ({target_lang}+en)"
    else:
        component_set = set(components)
        if "user_system" in component_set:
            user_conv = target_lang
        if "agent_system" in component_set:
            agent_conv = target_lang
        if "greeting" in component_set:
            greeting_lang = target_lang
        if "tools" in component_set:
            tool_lang = target_lang
        if {"policy", "db", "tasks"} & component_set:
            context_lang = target_lang

    return SeatauRunSettings(
        experiment=experiment,
        target_lang=target_lang,
        run_lang_id=run_lang_id,
        asset_mode=preset.asset_mode,
        lang_components=components,
        mixed_tools_config=mixed_tools_config,
        user_conversation=user_conv,
        agent_conversation=agent_conv,
        greeting=greeting_lang,
        tools=tool_lang,
        context=context_lang,
    )


def log_seatau_run_settings(
    settings: SeatauRunSettings,
    log_level: str = "INFO",
) -> None:
    """Emit SEA-TAU metadata to stdout via loguru."""
    logger.remove()
    logger.add(lambda msg: print(msg), level=log_level)

    mixed_tools_config = settings.mixed_tools_config or "none"
    logger.info(
        "SEA-TAU settings: experiment={experiment}, target_lang={target_lang}, "
        "run_lang_id={run_lang_id}, asset_mode={asset_mode}, "
        "lang_components={lang_components}, "
        "mixed_tools_config={mixed_tools_config}",
        experiment=settings.experiment,
        target_lang=settings.target_lang,
        run_lang_id=settings.run_lang_id,
        asset_mode=settings.asset_mode,
        lang_components=list(settings.lang_components),
        mixed_tools_config=mixed_tools_config,
    )
    logger.info(
        "SEA-TAU language surfaces: user_conversation={user_conversation}, "
        "agent_conversation={agent_conversation}, greeting={greeting}, "
        "tools={tools}, context(db/tasks/policy)={context}",
        user_conversation=settings.user_conversation,
        agent_conversation=settings.agent_conversation,
        greeting=settings.greeting,
        tools=settings.tools,
        context=settings.context,
    )


