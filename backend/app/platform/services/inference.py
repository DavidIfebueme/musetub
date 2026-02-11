from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.platform.config import settings


@dataclass(frozen=True)
class InferenceResponse:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int


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
    base_url = settings.inference_base_url.rstrip("/")

    headers = {
        "Authorization": f"Bearer {settings.inference_api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": resolved_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    timeout = httpx.Timeout(settings.inference_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()

    data = resp.json()
    choices = data.get("choices", [])
    text = ""
    if choices:
        message = choices[0].get("message", {})
        text = message.get("content", "") or ""

    usage = data.get("usage", {})

    return InferenceResponse(
        text=text.strip(),
        model=data.get("model", resolved_model),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
    )


async def vision_analysis(
    *,
    prompt: str,
    image_b64_list: list[str],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> InferenceResponse:
    content: list[dict] = [{"type": "text", "text": prompt}]
    for img_b64 in image_b64_list:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
        })

    messages = [{"role": "user", "content": content}]

    return await chat_completion(
        messages=messages,
        model=model or settings.inference_vision_model,
        temperature=temperature,
        max_tokens=max_tokens,
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
