from __future__ import annotations

import json
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.features.ai_agents.services.moderation import moderate_content
from app.features.ai_agents.services.pricing import compute_suggested_price_per_second_minor_units
from app.features.ai_agents.services.quality import (
    VISUAL_ANALYSIS_PROMPT,
    compute_composite_score,
    compute_quality_score,
    compute_technical_score,
    parse_llm_scores,
)
from app.platform.services.inference import is_configured, text_completion, vision_analysis
from app.platform.services.video_analysis import extract_keyframes, extract_metadata, frames_to_base64

logger = logging.getLogger(__name__)


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
    thumbnail_frame: bytes | None


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
    keyframes_b64: list[str] = []
    thumbnail_frame: bytes | None = None

    suffix = Path(filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        try:
            metadata = await extract_metadata(tmp_path)
            logger.info("ffprobe extracted metadata: duration=%.1fs resolution=%s bitrate_tier=%s codec=%s",
                        metadata.duration_seconds, metadata.resolution, metadata.bitrate_tier, metadata.codec)
        except Exception as exc:
            logger.warning("ffprobe metadata extraction failed: %s", exc)
            pass

        if metadata and metadata.has_video:
            try:
                frames = await extract_keyframes(tmp_path, count=4)
                if frames:
                    thumbnail_frame = frames[0]
                keyframes_b64 = frames_to_base64(frames)
                logger.info("Extracted %d keyframes from video", len(keyframes_b64))
            except Exception as exc:
                logger.warning("Keyframe extraction failed: %s", exc)
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
            if keyframes_b64:
                logger.info("Running vision analysis with %d keyframes via Gradient", len(keyframes_b64))
                response = await vision_analysis(
                    system_prompt=VISUAL_ANALYSIS_PROMPT,
                    user_prompt=context,
                    image_b64_list=keyframes_b64,
                )
            else:
                logger.info("Running text-only quality analysis via Gradient (no keyframes)")
                response = await text_completion(
                    system_prompt=VISUAL_ANALYSIS_PROMPT,
                    user_prompt=context,
                )
            visual_score, content_score, summary = parse_llm_scores(response.text)
            logger.info("Quality analysis complete: visual=%.1f content=%.1f summary=%s",
                        visual_score, content_score, summary[:80])
        except Exception as exc:
            logger.warning("Quality analysis failed: %s", exc)
            pass

    moderation_safe = True
    moderation_reason = ""

    if is_configured():
        try:
            logger.info("Running content moderation%s", " with vision" if keyframes_b64 else " (text only)")
            mod_result = await moderate_content(
                filename=filename,
                content_type=content_type,
                duration_seconds=duration,
                resolution=resolution,
                image_b64_list=keyframes_b64 or None,
            )
            moderation_safe = mod_result.safe
            moderation_reason = mod_result.reason
            logger.info("Moderation result: safe=%s reason=%s", moderation_safe, moderation_reason or "none")
        except Exception as exc:
            logger.warning("Moderation failed: %s", exc)
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

    logger.info("Analysis complete: quality_score=%d suggested_price=%d duration=%ds resolution=%s moderation_safe=%s",
                quality_score, suggested_price, duration, resolution, moderation_safe)

    return ContentAnalysisResult(
        duration_seconds=duration,
        resolution=resolution,
        bitrate_tier=bitrate_tier,
        quality_score=quality_score,
        suggested_price=suggested_price,
        moderation_safe=moderation_safe,
        moderation_reason=moderation_reason,
        analysis_summary=summary,
        thumbnail_frame=thumbnail_frame,
    )
