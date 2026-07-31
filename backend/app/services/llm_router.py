"""LLM router — NVIDIA NIM only, backed by the rotating API key pool.

Every request names the *agent* making it. The key pool ([key_pool.py]) maps
that agent to its own API key, so concurrent pipeline stages never share a
quota. When a key hits a 429 the pool parks it and the retry lands on a
different key instead of hammering the same wall.

There is deliberately no per-provider branching left: Groq has been removed
entirely and all inference goes to NVIDIA NIM.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

import httpx
from fastapi import HTTPException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.key_pool import NoKeysConfigured, key_pool

logger = logging.getLogger(__name__)

NVIDIA_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# Payload keys NVIDIA NIM accepts. Anything else is stripped before sending.
_VALID_PAYLOAD_KEYS = {
    "model", "messages", "temperature", "top_p", "n", "stream", "stop",
    "max_tokens", "presence_penalty", "frequency_penalty", "logit_bias",
    "user", "response_format", "seed", "tools", "tool_choice",
}

# Upper bound on a single completion. This is a real ceiling for the model, not
# the old blanket 2048 clamp that silently truncated every code generation and
# research synthesis.
MAX_COMPLETION_TOKENS = 32768

REQUEST_TIMEOUT = httpx.Timeout(connect=15.0, read=300.0, write=30.0, pool=15.0)

# Configure the shared key pool from settings on first import, so any caller
# gets a ready pool regardless of import order.
if key_pool.size == 0:
    key_pool.configure(settings.nvidia_api_keys)


# ── Model aliases ─────────────────────────────────────────────────────────
# Maps friendly/legacy names the UI or older code may still send onto the
# NVIDIA model actually in use. Unknown names pass through untouched so a raw
# NVIDIA model id always works.
def _model_aliases() -> dict:
    return {
        # Legacy Groq-era names still present in saved user settings.
        "llama-3.1-70b-versatile": settings.DEFAULT_CHAT_MODEL,
        "llama-3.3-70b-versatile": settings.DEFAULT_CHAT_MODEL,
        "llama3-70b": settings.DEFAULT_CHAT_MODEL,
        "llama3-8b": settings.FAST_MODEL,
        "mixtral": settings.DEFAULT_CHAT_MODEL,
        "gemma": settings.FAST_MODEL,
        "z-ai/glm-5.2": settings.CODER_MODEL,
        # Semantic aliases used across the agent pipelines.
        "default": settings.DEFAULT_CHAT_MODEL,
        "reasoning": settings.REASONING_MODEL,
        "fast": settings.FAST_MODEL,
        "planner_agent": settings.PLANNER_MODEL,
        "coder_agent": settings.CODER_MODEL,
        "research_agent": settings.DEEP_RESEARCH_DEFAULT_MODEL,
    }


def resolve_model(name: Optional[str]) -> str:
    """Resolve an alias (or raw id) to a concrete NVIDIA model id."""
    if not name:
        return settings.DEFAULT_CHAT_MODEL
    return _model_aliases().get(name, name)


def _build_payload(payload: dict, stream: bool) -> dict:
    """Strip unsupported keys, resolve the model, and clamp max_tokens sanely."""
    clean = {k: v for k, v in payload.items() if k in _VALID_PAYLOAD_KEYS}
    clean["model"] = resolve_model(payload.get("model"))
    clean["stream"] = stream

    requested = clean.get("max_tokens")
    if requested is None:
        clean["max_tokens"] = 4096
    else:
        clean["max_tokens"] = max(1, min(int(requested), MAX_COMPLETION_TOKENS))
    return clean


def _is_rate_limit(status_code: Optional[int], message: str) -> bool:
    if status_code in (429, 402):
        return True
    lowered = message.lower()
    return "429" in lowered or "rate limit" in lowered or "quota" in lowered


class LLMError(HTTPException):
    """Raised on an upstream failure. Retryable by Tenacity."""

    def __init__(self, detail: str, status_code: int = 502):
        super().__init__(status_code=status_code, detail=detail)


# ── Core call ─────────────────────────────────────────────────────────────
@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(LLMError),
    reraise=True,
)
async def call_llm(
    request_type: str,
    payload: dict,
    agent: str = "default",
    stream: bool = False,
    key_group: Optional[str] = None,
):
    """Call NVIDIA NIM.

    Args:
        request_type: free-text label for logging (e.g. "chat", "code_generate").
        payload: OpenAI-shaped request body.
        agent: logical agent name — decides which pooled API key is used.
        stream: when True returns an async generator yielding content deltas.
        key_group: legacy alias for `agent`, kept for backward compatibility.

    Returns:
        dict (OpenAI-shaped response) when stream=False,
        AsyncGenerator[str] of content deltas when stream=True.
    """
    agent = key_group or agent
    body = _build_payload(payload, stream)

    if stream:
        return _stream_completion(request_type, body, agent)
    return await _complete(request_type, body, agent)


async def _complete(request_type: str, body: dict, agent: str) -> dict:
    """Non-streaming completion."""
    try:
        async with key_pool.lease(agent) as lease:
            headers = {
                "Authorization": f"Bearer {lease.key}",
                "Content-Type": "application/json",
            }
            logger.info(
                "LLM '%s' agent=%s model=%s %s",
                request_type, agent, body["model"], lease.label,
            )
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    response = await client.post(NVIDIA_CHAT_URL, headers=headers, json=body)

                if response.status_code == 200:
                    lease.mark_success()
                    return response.json()

                detail = response.text[:500]
                if _is_rate_limit(response.status_code, detail):
                    lease.mark_rate_limited()
                    raise LLMError(
                        f"NVIDIA rate limit ({response.status_code}) on {lease.label}: {detail}"
                    )
                lease.mark_error()
                raise LLMError(f"NVIDIA error {response.status_code}: {detail}")

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                lease.mark_error()
                raise LLMError(f"NVIDIA transport failure: {exc}") from exc

    except NoKeysConfigured as exc:
        # Not retryable — no amount of backoff produces a key.
        logger.error("LLM '%s' agent=%s: %s", request_type, agent, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def _stream_completion(
    request_type: str, body: dict, agent: str
) -> AsyncGenerator[str, None]:
    """Streaming completion — yields content deltas as plain strings."""
    try:
        async with key_pool.lease(agent) as lease:
            headers = {
                "Authorization": f"Bearer {lease.key}",
                "Content-Type": "application/json",
            }
            logger.info(
                "LLM stream '%s' agent=%s model=%s %s",
                request_type, agent, body["model"], lease.label,
            )
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    async with client.stream(
                        "POST", NVIDIA_CHAT_URL, headers=headers, json=body
                    ) as response:
                        if response.status_code != 200:
                            detail = (await response.aread()).decode()[:500]
                            if _is_rate_limit(response.status_code, detail):
                                lease.mark_rate_limited()
                            else:
                                lease.mark_error()
                            logger.error(
                                "NVIDIA stream error %s on %s: %s",
                                response.status_code, lease.label, detail,
                            )
                            yield f"\n\n[Model error {response.status_code}] {detail}"
                            return

                        buffer = ""
                        async for chunk in response.aiter_text():
                            if not chunk:
                                continue
                            buffer += chunk
                            lines = buffer.split("\n")
                            buffer = lines.pop()
                            for line in lines:
                                line = line.strip()
                                if not line.startswith("data:"):
                                    continue
                                data_str = line[5:].strip()
                                if not data_str or data_str == "[DONE]":
                                    continue
                                try:
                                    delta = (
                                        json.loads(data_str)
                                        .get("choices", [{}])[0]
                                        .get("delta", {})
                                        .get("content", "")
                                    )
                                except (json.JSONDecodeError, IndexError, AttributeError):
                                    # Malformed SSE frame — skip it, keep streaming.
                                    continue
                                if delta:
                                    yield delta
                        lease.mark_success()

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                lease.mark_error()
                logger.error("NVIDIA stream transport failure: %s", exc)
                yield f"\n\n[Connection error] {exc}"
            except asyncio.CancelledError:
                # Client disconnected — release the key without penalising it.
                lease.mark_success()
                raise

    except NoKeysConfigured as exc:
        logger.error("LLM stream '%s' agent=%s: %s", request_type, agent, exc)
        yield f"\n\n[Configuration error] {exc}"


# ── Convenience helper ────────────────────────────────────────────────────
async def complete_text(
    messages: list,
    agent: str = "default",
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 4096,
    response_format: Optional[dict] = None,
) -> str:
    """Run a non-streaming completion and return just the text content.

    This is the ergonomic entry point for agent code, which almost always wants
    a string back rather than the full OpenAI envelope.
    """
    payload = {
        "model": model or settings.DEFAULT_CHAT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    result = await call_llm(agent, payload, agent=agent, stream=False)
    try:
        return result["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected LLM response shape for agent=%s: %s", agent, str(result)[:300])
        return ""
