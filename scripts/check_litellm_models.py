#!/usr/bin/env python3
"""Smoke-test whether LiteLLM can call one or more configured models.

Examples:
    uv run python scripts/check_litellm_models.py
    uv run python scripts/check_litellm_models.py --model gemini/gemini-2.5-flash
    uv run python scripts/check_litellm_models.py \
        --model vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas
    python scripts/check_litellm_models.py \
        --model vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas \
        --prompt "Write me a novel long 10 pages"
    python scripts/check_litellm_models.py \
        --model openai/gpt-5-mini \
        --prompt "Write me a novel long 10 pages"
    python scripts/check_litellm_models.py \
        --api-base http://localhost:8000/v1 \
        --model "/project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"
    python scripts/check_litellm_models.py \
        --api-base http://localhost:8000/v1 \
        --model "openai//project/lt200394-thllmV/jab/seacrowd/models/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"

    uv run python scripts/check_litellm_models.py --vertex-location us-south1

Gemini usually requires GEMINI_API_KEY or GOOGLE_API_KEY.
Vertex AI usually requires VERTEXAI_PROJECT, VERTEXAI_LOCATION, and ADC or
GOOGLE_APPLICATION_CREDENTIALS.
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from typing import Any

import litellm
from litellm import completion

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is a project dependency.
    load_dotenv = None


DEFAULT_MODELS = [
    "vertex_ai/gemini/gemini-2.5-flash",
    "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas",
]
DEFAULT_QWEN_VERTEX_LOCATION = "us-south1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether LiteLLM can complete with selected models."
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help=(
            "LiteLLM model name to test. Repeat this flag for multiple models. "
            f"Defaults to: {', '.join(DEFAULT_MODELS)}"
        ),
    )
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: OK",
        help="Prompt sent to each model.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8192,
        help="Maximum output tokens for each smoke test.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--vertex-location",
        help=(
            "Vertex AI location to pass to LiteLLM for every Vertex model. "
            "If omitted, Qwen Vertex MaaS models default to "
            f"{DEFAULT_QWEN_VERTEX_LOCATION}; other models use VERTEXAI_LOCATION."
        ),
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("LITELLM_API_BASE") or os.getenv("OPENAI_API_BASE"),
        help=(
            "OpenAI-compatible API base URL to pass to LiteLLM, e.g. "
            "http://localhost:8000/v1. Defaults to LITELLM_API_BASE or "
            "OPENAI_API_BASE."
        ),
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        help=(
            "API key to pass to LiteLLM. For local servers that ignore auth, "
            "a dummy key is used when --api-base is set and no key is provided."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full Python traceback for failures.",
    )
    return parser.parse_args()


def response_text(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except Exception:
        return ""
    if content is None:
        return ""
    return str(content).strip()


def default_vertex_location(model: str) -> str | None:
    if model.startswith("vertex_ai/qwen/"):
        return DEFAULT_QWEN_VERTEX_LOCATION
    return None


def normalize_model_for_api_base(model: str, api_base: str | None) -> str:
    """Preserve exact OpenAI-compatible model paths for LiteLLM.

    LiteLLM uses prefixes such as ``openai/`` to choose a provider. If an
    OpenAI-compatible server expects a model ID that starts with ``/``, pass it
    as ``openai//...`` so the provider prefix is removed but the model path
    still begins with ``/``.
    """
    if api_base and model.startswith("/"):
        return f"openai/{model}"
    return model


def run_check(
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
    vertex_location: str | None,
    api_base: str | None,
    api_key: str | None,
) -> bool:
    completion_kwargs: dict[str, Any] = {}
    if vertex_location:
        completion_kwargs["vertex_location"] = vertex_location
    if api_base:
        completion_kwargs["api_base"] = api_base
        completion_kwargs["api_key"] = api_key or "sk-local"
    elif api_key:
        completion_kwargs["api_key"] = api_key

    location_suffix = f" in {vertex_location}" if vertex_location else ""
    normalized_model = normalize_model_for_api_base(model, api_base)
    api_base_suffix = f" via {api_base}" if api_base else ""
    print(
        f"\nChecking {model}{location_suffix}{api_base_suffix} ...",
        flush=True,
    )
    response = completion(
        model=normalized_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
        timeout=timeout,
        num_retries=0,
        **completion_kwargs,
    )

    text = response_text(response)
    usage = response.get("usage") if hasattr(response, "get") else None

    print("PASS")
    if text:
        print(f"Response: {text}")
    if usage:
        print(f"Usage: {usage}")
    return True


def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = parse_args()

    litellm.drop_params = True

    models = args.models or DEFAULT_MODELS
    failed = False

    for model in models:
        vertex_location = args.vertex_location or default_vertex_location(model)
        try:
            run_check(
                model=model,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                vertex_location=vertex_location,
                api_base=args.api_base,
                api_key=args.api_key,
            )
        except Exception as exc:
            failed = True
            print("FAIL")
            print(f"{type(exc).__name__}: {exc}")
            if (
                args.api_base
                and model.startswith("openai/")
                and not model.startswith("openai//")
            ):
                print(
                    "Hint: if the backend model ID starts with '/', use "
                    "'openai//...' or pass the raw '/...' model path."
                )
            if args.verbose:
                traceback.print_exc()

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
