"""Expose a local OpenAI-compatible proxy on 127.0.0.1:8000.

This is a fallback for environments where the remote vLLM job is unavailable.
It keeps the local API shape that SEA-Tau expects and forwards requests to an
upstream chat-completions provider.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

APP_HOST = "127.0.0.1"
APP_PORT = 8000
LISTED_MODEL_NAME = os.getenv(
    "LOCAL_USER_LLM_MODEL_NAME", "Qwen3-235B-A22B-Instruct-2507-FP8"
)
UPSTREAM_MODEL = os.getenv(
    "LOCAL_USER_LLM_UPSTREAM_MODEL", "qwen/qwen3.6-35b-a3b"
)
UPSTREAM_API_BASE = os.getenv(
    "LOCAL_USER_LLM_UPSTREAM_API_BASE", "https://openrouter.ai/api/v1"
).rstrip("/")
UPSTREAM_API_KEY_ENV = os.getenv("LOCAL_USER_LLM_UPSTREAM_API_KEY_ENV", "OPENROUTER_API_KEY")
UPSTREAM_API_KEY = os.getenv(UPSTREAM_API_KEY_ENV, "").strip()

app = FastAPI()


def _models_payload() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": LISTED_MODEL_NAME,
                "object": "model",
                "owned_by": "proxy",
            }
        ],
    }


@app.get("/v1/models")
async def list_models() -> JSONResponse:
    return JSONResponse(_models_payload())


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True, "model": LISTED_MODEL_NAME})


async def _forward_chat_completion(request: Request) -> Response:
    if not UPSTREAM_API_KEY:
        raise HTTPException(
            status_code=500,
            detail=f"Missing upstream API key in ${UPSTREAM_API_KEY_ENV}",
        )

    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Expected a JSON object body")

    payload["model"] = UPSTREAM_MODEL
    # The user simulator expects visible message content. Some OpenRouter Qwen
    # reasoning models can spend the whole completion budget on reasoning and
    # return content=null unless reasoning is explicitly disabled.
    payload.setdefault("reasoning", {"effort": "none", "exclude": True})
    payload.setdefault("include_reasoning", False)
    headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://127.0.0.1:8000",
        "X-Title": "seatau-local-user-llm-proxy",
    }
    upstream_url = f"{UPSTREAM_API_BASE}/chat/completions"
    stream = bool(payload.get("stream"))

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
        if stream:
            upstream = client.stream(
                "POST",
                upstream_url,
                json=payload,
                headers=headers,
            )
            upstream_response = await upstream.__aenter__()

            if upstream_response.status_code >= 400:
                body = await upstream_response.aread()
                await upstream.__aexit__(None, None, None)
                return Response(
                    content=body,
                    status_code=upstream_response.status_code,
                    media_type=upstream_response.headers.get(
                        "content-type", "application/json"
                    ),
                )

            async def body_iter():
                async for chunk in upstream_response.aiter_bytes():
                    yield chunk
                await upstream.__aexit__(None, None, None)

            return StreamingResponse(
                body_iter(),
                status_code=upstream_response.status_code,
                media_type=upstream_response.headers.get(
                    "content-type", "text/event-stream"
                ),
            )

        upstream_response = await client.post(
            upstream_url,
            json=payload,
            headers=headers,
        )

    content_type = upstream_response.headers.get("content-type", "application/json")
    if upstream_response.status_code >= 400:
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=content_type,
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=content_type,
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Response:
    return await _forward_chat_completion(request)


@app.post("/v1/completions")
async def completions(request: Request) -> Response:
    return await _forward_chat_completion(request)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="info")


if __name__ == "__main__":
    main()
