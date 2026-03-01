from __future__ import annotations

import argparse
import os
import sys

from translation.config import default_config
from translation.pipeline import run_pipeline


def _load_dotenv() -> None:
    """
    Best-effort .env loading.
    Uses python-dotenv when available and stays non-fatal if not installed.
    """
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate Tau2 domain assets with selective rules via LiteLLM."
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        required=True,
        help="Domain names, e.g. mock telecom retail",
    )
    parser.add_argument(
        "--source-language",
        default="English",
        help="Source language label for the model prompt.",
    )
    parser.add_argument(
        "--target-language",
        default="Thai",
        help="Target language label for the model prompt.",
    )
    parser.add_argument(
        "--data-domains-root",
        default="data/tau2/domains",
        help="Root directory for domain data folders.",
    )
    parser.add_argument(
        "--src-domains-root",
        default="src/tau2/domains",
        help="Root directory for domain source folders.",
    )
    parser.add_argument(
        "--output-root",
        default="translation/output",
        help="Where translated files are written.",
    )
    parser.add_argument(
        "--model",
        default="gemini-3-flash-preview",
        help="LiteLLM model identifier (provider/model or proxy-routed model).",
    )
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="Environment variable containing API key for the target provider/proxy.",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help="Optional LiteLLM/OpenAI-compatible proxy base URL.",
    )
    parser.add_argument(
        "--api-version",
        default=None,
        help="Optional API version (useful for Azure OpenAI).",
    )
    parser.add_argument(
        "--max-rpm",
        type=float,
        default=5.0,
        help="Maximum requests per minute. Default 5.0 (Gemini free tier safe).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=24,
        help="Number of segments per API call.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and preview segments without calling the LLM.",
    )
    parser.add_argument(
        "--max-preview",
        type=int,
        default=20,
        help="How many segments to print during dry run.",
    )
    return parser


def _infer_api_key_env(model: str) -> str:
    model = model.strip().lower()
    if model.startswith("azure/"):
        return "AZURE_API_KEY"
    if model.startswith("openai/"):
        return "OPENAI_API_KEY"
    if model.startswith("anthropic/"):
        return "ANTHROPIC_API_KEY"
    if model.startswith("gemini/") or model.startswith("gemini-"):
        return "GEMINI_API_KEY"
    return "GEMINI_API_KEY"


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    api_key_env = args.api_key_env or _infer_api_key_env(args.model)
    api_base = args.api_base
    api_version = args.api_version
    if args.model.strip().lower().startswith("azure/"):
        if api_base is None:
            api_base = os.getenv("AZURE_API_BASE")
        if api_version is None:
            api_version = os.getenv("AZURE_API_VERSION")
    else:
        if api_base is None:
            api_base = os.getenv("LITELLM_API_BASE")

    config = default_config(
        domains=args.domains,
        source_language=args.source_language,
        target_language=args.target_language,
        data_domains_root=args.data_domains_root,
        src_domains_root=args.src_domains_root,
        output_root=args.output_root,
        model=args.model,
        api_key_env=api_key_env,
        api_base=api_base,
        api_version=api_version,
        max_rpm=args.max_rpm,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        max_preview=args.max_preview,
    )
    return run_pipeline(config)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
