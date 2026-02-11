from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.features.ai_agents.services.moderation import moderate_content
from app.features.ai_agents.services.pricing import compute_suggested_price_per_second_minor_units
from app.features.ai_agents.services.quality import (
    QUALITY_ANALYSIS_PROMPT,
    compute_composite_score,
    compute_quality_score,
    compute_technical_score,
    parse_llm_scores,
)
from app.platform.services.inference import is_configured, text_completion
from app.platform.services.video_analysis import extract_metadata


@dataclass(frozen=True)
class ContentAnalysisResult:
    duration_seconds: int
    resolution: str
    bitrate_tier: str
    quality_score: int
    suggested_price: int
    moderation_safe: bool
    moderation_reason: str
    analysis_summary: str


async def analyze_upload(
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    engagement_intent: str,
    form_duration: int | None = None,
    form_resolution: str | None = None,
    form_bitrate_tier: str | None = None,
) -> ContentAnalysisResult:
    metadata = None

    suffix = Path(filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        try:
            metadata = await extract_metadata(tmp_path)
        except Exception:
            pass
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if metadata:
        duration = max(int(metadata.duration_seconds), 0)
        resolution = metadata.resolution
        bitrate_tier = metadata.bitrate_tier
        technical_score = compute_technical_score(metadata)
    else:
        duration = form_duration or 0
        resolution = form_resolution or "unknown"
        bitrate_tier = form_bitrate_tier or "low"
        technical_score = 5.0

    visual_score = 5.0
    content_score = 5.0
    summary = ""

    if metadata and is_configured():
        try:
            context = json.dumps({
                "filename": filename,
                "duration_seconds": duration,
                "resolution": resolution,
                "bitrate_tier": bitrate_tier,
                "codec": metadata.codec,
                "framerate": metadata.framerate,
                "width": metadata.width,
                "height": metadata.height,
                "bitrate": metadata.bitrate,
                "has_audio": metadata.has_audio,
                "content_type": content_type,
                "engagement_intent": engagement_intent,
            })
            response = await text_completion(
                system_prompt=QUALITY_ANALYSIS_PROMPT,
                user_prompt=context,
            )
            visual_score, content_score, summary = parse_llm_scores(response.text)
        except Exception:
            pass

    moderation_safe = True
    moderation_reason = ""

    if is_configured():
        try:
            mod_result = await moderate_content(
                filename=filename,
                content_type=content_type,
                duration_seconds=duration,
                resolution=resolution,
            )
            moderation_safe = mod_result.safe
            moderation_reason = mod_result.reason
        except Exception:
            pass

    if not metadata and not is_configured():
        quality_score = compute_quality_score(
            duration_seconds=duration,
            resolution=resolution,
            bitrate_tier=bitrate_tier,
            content_type=content_type,
            engagement_intent=engagement_intent,
        )
    else:
        quality_score = compute_composite_score(
            technical_score=technical_score,
            visual_score=visual_score,
            content_score=content_score,
        )

    suggested_price = compute_suggested_price_per_second_minor_units(quality_score=quality_score)

    return ContentAnalysisResult(
        duration_seconds=duration,
        resolution=resolution,
        bitrate_tier=bitrate_tier,
        quality_score=quality_score,
        suggested_price=suggested_price,
        moderation_safe=moderation_safe,
        moderation_reason=moderation_reason,
        analysis_summary=summary,
    )
