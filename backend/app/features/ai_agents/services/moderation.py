from __future__ import annotations

import json
from dataclasses import dataclass

from app.platform.services.inference import is_configured, vision_analysis


MODERATION_PROMPT = (
    "Analyze these video keyframes for content policy compliance. "
    "Check for: explicit/sexual content, graphic violence, hate symbols, "
    "dangerous activities, visible watermarks from other platforms indicating reposted content. "
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


async def moderate_content(image_b64_list: list[str]) -> ModerationResult:
    if not image_b64_list:
        return ModerationResult(safe=True, flags=[], confidence=0.0, reason="No frames to analyze")

    if not is_configured():
        return ModerationResult(safe=True, flags=[], confidence=0.0, reason="Moderation not configured")

    try:
        response = await vision_analysis(
            prompt=MODERATION_PROMPT,
            image_b64_list=image_b64_list,
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
