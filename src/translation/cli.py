from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from translation.config import SKIPPED_DOMAINS
from translation.models import (
    COMPONENT_CHOICES,
    DEFAULT_API_BASE,
    DEFAULT_API_KEY_ENV,
    DEFAULT_BATCH_SIZE,
    DEFAULT_DATA_DOMAINS_ROOT,
    DEFAULT_MAX_PREVIEW,
    DEFAULT_MAX_RPM,
    DEFAULT_MODEL,
    DEFAULT_RETRIES,
    DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_SRC_DOMAINS_ROOT,
    DEFAULT_TIMEOUT_S,
    PipelineConfig,
    normalize_components,
)
from translation.pipeline import run_pipeline

LANGUAGES_PATH = Path("data/languages.json")


def _load_dotenv() -> None:
    """Best-effort .env loading."""
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv()


def _load_language_registry() -> dict[str, dict[str, str]]:
    """Load language configs from data/languages.json."""
    with LANGUAGES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Translate Tau2 domain assets with selective rules via LiteLLM.",
)
@click.option(
    "--domains",
    "domains",
    multiple=True,
    required=True,
    metavar="DOMAIN",
    help="Domain names to translate. Repeat the option, e.g. --domains retail --domains airline.",
)
@click.option(
    "--lang-id",
    type=click.Choice(sorted(_load_language_registry().keys()), case_sensitive=True),
    required=True,
    help="Target language code from data/languages.json.",
)
@click.option(
    "--source-language",
    default=DEFAULT_SOURCE_LANGUAGE,
    show_default=True,
    help="Source language label for the model prompt.",
)
@click.option(
    "--components",
    multiple=True,
    type=click.Choice(COMPONENT_CHOICES, case_sensitive=True),
    default=("all",),
    show_default=True,
    help="Asset groups to translate. Alias: context=policy+db+tasks, all=all components.",
)
@click.option(
    "--data-domains-root",
    default=str(DEFAULT_DATA_DOMAINS_ROOT),
    show_default=True,
    help="Root directory for domain data folders.",
)
@click.option(
    "--src-domains-root",
    default=str(DEFAULT_SRC_DOMAINS_ROOT),
    show_default=True,
    help="Root directory for domain source folders.",
)
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="LiteLLM model identifier (provider/model or proxy-routed model).",
)
@click.option(
    "--api-key-env",
    default=DEFAULT_API_KEY_ENV,
    show_default=True,
    help="Environment variable containing the API key (e.g. OPENROUTER_API_KEY, LITELLM_MASTER_KEY).",
)
@click.option(
    "--api-base",
    default=DEFAULT_API_BASE,
    show_default=True,
    help="Optional LiteLLM/OpenAI-compatible proxy base URL.",
)
@click.option(
    "--api-version",
    default=None,
    help="Optional API version (useful for Azure OpenAI).",
)
@click.option(
    "--max-rpm",
    type=float,
    default=DEFAULT_MAX_RPM,
    show_default=True,
    help="Maximum requests per minute.",
)
@click.option(
    "--batch-size",
    type=int,
    default=DEFAULT_BATCH_SIZE,
    show_default=True,
    help="Number of segments per API call.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Extract and preview segments without calling the LLM.",
)
@click.option(
    "--max-preview",
    type=int,
    default=DEFAULT_MAX_PREVIEW,
    show_default=True,
    help="How many segments to print during dry run.",
)
@click.option(
    "--timeout",
    "timeout_s",
    type=int,
    default=DEFAULT_TIMEOUT_S,
    show_default=True,
    help="Request timeout in seconds.",
)
@click.option(
    "--retries",
    type=int,
    default=DEFAULT_RETRIES,
    show_default=True,
    help="Number of retries on failure.",
)
def cli(
    domains: tuple[str, ...],
    lang_id: str,
    source_language: str,
    components: tuple[str, ...],
    data_domains_root: str,
    src_domains_root: str,
    model: str,
    api_key_env: str,
    api_base: str | None,
    api_version: str | None,
    max_rpm: float,
    batch_size: int,
    dry_run: bool,
    max_preview: int,
    timeout_s: int,
    retries: int,
) -> int:
    _load_dotenv()

    # Resolve display name from language registry
    lang_registry = _load_language_registry()
    lang_config = lang_registry[lang_id]
    target_language = lang_config["display_name"]
    unsupported = sorted(set(domains) & SKIPPED_DOMAINS)
    if unsupported:
        raise click.UsageError(
            "Translation pipeline does not support these domains: "
            + ", ".join(unsupported)
        )

    resolved_api_base = api_base or os.getenv("LITELLM_API_BASE")

    config = PipelineConfig(
        domains=list(domains),
        target_language=target_language,
        lang_id=lang_id,
        source_language=source_language,
        components=normalize_components(components),
        data_domains_root=Path(data_domains_root),
        src_domains_root=Path(src_domains_root),
        model=model,
        api_key_env=api_key_env,
        api_base=resolved_api_base,
        api_version=api_version,
        max_rpm=max_rpm,
        batch_size=batch_size,
        dry_run=dry_run,
        max_preview=max_preview,
        timeout_s=timeout_s,
        retries=retries,
    )
    return run_pipeline(config)


def main(argv: list[str] | None = None) -> int:
    try:
        result = cli.main(args=argv, standalone_mode=False)
        if isinstance(result, int):
            return result
        return 0
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
