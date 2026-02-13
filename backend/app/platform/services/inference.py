from __future__ import annotations

import logging
from dataclasses import dataclass

from gradient import AsyncGradient

from app.platform.config import settings

logger = logging.getLogger(__name__)

_client: AsyncGradient | None = None


def _is_claude_family_model(model: str) -> bool:
    value = model.lower()
    return "claude" in value or "anthropic" in value


@dataclass(frozen=True)
class InferenceResponse:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int


def _get_client() -> AsyncGradient:
    global _client
    if _client is None:
        _client = AsyncGradient(
            model_access_key=settings.inference_api_key,
            timeout=settings.inference_timeout_seconds,
        )
    return _client


def is_configured() -> bool:
    return bool(settings.inference_api_key)


async def chat_completion(
    *,
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> InferenceResponse:
    resolved_model = model or settings.inference_model
    client = _get_client()

    response = await client.chat.completions.create(
        messages=messages,
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )

    text = ""
    if response.choices:
        msg = response.choices[0].message
        if msg and msg.content:
            text = msg.content

    prompt_tokens = 0
    completion_tokens = 0
    if response.usage:
        prompt_tokens = response.usage.prompt_tokens or 0
        completion_tokens = response.usage.completion_tokens or 0

    return InferenceResponse(
        text=text.strip(),
        model=response.model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )


async def text_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 512,
) -> InferenceResponse:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return await chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def vision_analysis(
    *,
    system_prompt: str,
    user_prompt: str,
    image_b64_list: list[str],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> InferenceResponse:
    resolved_model = model or settings.inference_vision_model

    if _is_claude_family_model(resolved_model):
        logger.warning(
            "Vision model '%s' on chat.completions does not accept image_url blocks; using text-only fallback.",
            resolved_model,
        )
        user_content: str | list[dict] = user_prompt
    else:
        content_parts: list[dict] = [{"type": "text", "text": user_prompt}]
        for b64 in image_b64_list:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
        user_content = content_parts

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    return await chat_completion(
        messages=messages,
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
