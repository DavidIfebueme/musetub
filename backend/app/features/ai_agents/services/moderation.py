from __future__ import annotations

import json
from dataclasses import dataclass

from app.platform.services.inference import is_configured, text_completion, vision_analysis


MODERATION_PROMPT = (
    "You are a content moderation agent for a video streaming platform. "
    "Analyze the provided video keyframes and metadata to assess whether the content "
    "complies with content policy. Look for violence, nudity, hate speech indicators, "
    "dangerous activities, or any other policy violations visible in the frames. "
    "Return ONLY valid JSON with no extra text: "
    '{"safe": true, "flags": [], "confidence": 0.0, "reason": ""} '
    "where safe is boolean, flags is a list of policy violation categories, "
    "confidence is 0.0-1.0, and reason explains any flags."
)


@dataclass(frozen=True)
class ModerationResult:
    safe: bool
    flags: list[str]
    confidence: float
    reason: str


async def moderate_content(
    *,
    filename: str,
    content_type: str,
    duration_seconds: int,
    resolution: str,
    image_b64_list: list[str] | None = None,
) -> ModerationResult:
    if not is_configured():
        return ModerationResult(safe=True, flags=[], confidence=0.0, reason="Moderation not configured")

    context = json.dumps({
        "filename": filename,
        "content_type": content_type,
        "duration_seconds": duration_seconds,
        "resolution": resolution,
    })

    try:
        if image_b64_list:
            response = await vision_analysis(
                system_prompt=MODERATION_PROMPT,
                user_prompt=context,
                image_b64_list=image_b64_list,
                temperature=0.1,
                max_tokens=512,
            )
        else:
            response = await text_completion(
                system_prompt=MODERATION_PROMPT,
                user_prompt=context,
                temperature=0.1,
                max_tokens=512,
            )
        data = json.loads(response.text)
        return ModerationResult(
            safe=bool(data.get("safe", True)),
            flags=list(data.get("flags", [])),
            confidence=float(data.get("confidence", 0.0)),
            reason=str(data.get("reason", "")),
        )
    except Exception:
        return ModerationResult(safe=True, flags=[], confidence=0.0, reason="Moderation unavailable")
