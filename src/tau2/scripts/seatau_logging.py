"""SEA-TAU run metadata logging helpers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from loguru import logger

MIXED_TOOL_EXPERIMENTS = {
    "mixed_tools",
    "mixed_tools_2lang",
    "mixed_tools_3lang",
    "mixed_tools_5lang",
}


@dataclass(frozen=True)
class SeatauRunSettings:
    """Resolved SEA-TAU metadata for one tau2 run invocation."""

    experiment: str
    target_lang: str
    run_lang_id: str
    lang_components: tuple[str, ...]
    mixed_tools_config: str | None
    user_conversation: str
    agent_conversation: str
    greeting: str
    tools: str
    context: str

def build_seatau_run_settings(
    experiment: str,
    target_lang: str,
    run_lang_id: str,
    lang_components: list[str] | tuple[str, ...],
    mixed_tools_config: str | None = None,
) -> SeatauRunSettings:
    """Resolve SEA-TAU display metadata for one run."""
    components = tuple(lang_components)
    user_conv = "English"
    agent_conv = "English"
    greeting_lang = "English"
    tool_lang = "English"
    context_lang = "English"

    if experiment in MIXED_TOOL_EXPERIMENTS:
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
        "run_lang_id={run_lang_id}, lang_components={lang_components}, "
        "mixed_tools_config={mixed_tools_config}",
        experiment=settings.experiment,
        target_lang=settings.target_lang,
        run_lang_id=settings.run_lang_id,
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


def main() -> None:
    """CLI entry point for shell wrappers."""
    parser = argparse.ArgumentParser(
        description="Emit SEA-TAU run metadata through loguru."
    )
    parser.add_argument("--domain", default="")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--target-lang", required=True)
    parser.add_argument("--run-lang-id", required=True)
    parser.add_argument("--mixed-tools-config", default=None)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--lang-components", nargs="*", default=[])
    args = parser.parse_args()

    settings = build_seatau_run_settings(
        experiment=args.experiment,
        target_lang=args.target_lang,
        run_lang_id=args.run_lang_id,
        lang_components=args.lang_components,
        mixed_tools_config=args.mixed_tools_config,
    )
    log_seatau_run_settings(settings=settings, log_level=args.log_level)


if __name__ == "__main__":
    main()
