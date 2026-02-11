from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.platform.services.video_analysis import VideoMetadata


@dataclass(frozen=True)
class QualityResult:
    score: int
    technical_score: float
    visual_score: float
    content_score: float
    summary: str


VISUAL_ANALYSIS_PROMPT = (
    "Analyze these video keyframes for visual and content quality. "
    "Consider: image clarity, sharpness, lighting, color grading, composition, production value. "
    "For content, consider educational/entertainment value and originality. "
    "Return ONLY valid JSON with no extra text: "
    '{"visual_score": 0.0, "content_score": 0.0, "summary": "1-2 sentence analysis"} '
    "where scores range from 0.0 to 10.0."
)


def compute_technical_score(metadata: VideoMetadata) -> float:
    score = 0.0

    if metadata.height >= 2160:
        score += 4.0
    elif metadata.height >= 1440:
        score += 3.5
    elif metadata.height >= 1080:
        score += 3.0
    elif metadata.height >= 720:
        score += 2.0
    elif metadata.height >= 480:
        score += 1.0
    else:
        score += 0.5

    if metadata.bitrate >= 15_000_000:
        score += 3.0
    elif metadata.bitrate >= 8_000_000:
        score += 2.5
    elif metadata.bitrate >= 4_000_000:
        score += 2.0
    elif metadata.bitrate >= 2_000_000:
        score += 1.5
    elif metadata.bitrate >= 1_000_000:
        score += 1.0
    else:
        score += 0.5

    modern_codecs = {"h265", "hevc", "av1", "vp9"}
    good_codecs = {"h264", "avc", "vp8"}
    codec_lower = metadata.codec.lower()
    if codec_lower in modern_codecs:
        score += 1.5
    elif codec_lower in good_codecs:
        score += 1.0
    else:
        score += 0.5

    if metadata.framerate >= 60:
        score += 1.5
    elif metadata.framerate >= 30:
        score += 1.0
    elif metadata.framerate >= 24:
        score += 0.75
    else:
        score += 0.25

    return min(score, 10.0)


def parse_llm_scores(raw: str) -> tuple[float, float, str]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return 5.0, 5.0, "Analysis unavailable"

    visual = float(data.get("visual_score", 5.0))
    content = float(data.get("content_score", 5.0))
    summary = str(data.get("summary", ""))

    visual = max(0.0, min(10.0, visual))
    content = max(0.0, min(10.0, content))

    return visual, content, summary


def compute_composite_score(
    *,
    technical_score: float,
    visual_score: float,
    content_score: float,
) -> int:
    raw = (technical_score * 0.3) + (visual_score * 0.5) + (content_score * 0.2)
    clamped = max(1.0, min(10.0, raw))
    return round(clamped)


def build_quality_result(
    *,
    technical_score: float,
    visual_score: float,
    content_score: float,
    summary: str,
) -> QualityResult:
    score = compute_composite_score(
        technical_score=technical_score,
        visual_score=visual_score,
        content_score=content_score,
    )
    return QualityResult(
        score=score,
        technical_score=technical_score,
        visual_score=visual_score,
        content_score=content_score,
        summary=summary,
    )


def compute_quality_score(
    *,
    duration_seconds: int,
    resolution: str,
    bitrate_tier: str,
    content_type: str,
    engagement_intent: str,
) -> int:
    score = 4

    res = resolution.strip().lower().replace(" ", "")
    if res in {"2160p", "4k"}:
        score += 6
    elif res == "1440p":
        score += 5
    elif res == "1080p":
        score += 4
    elif res == "720p":
        score += 2
    elif res == "480p":
        score += 0
    else:
        score -= 1

    tier = bitrate_tier.strip().lower()
    if tier in {"high", "h"}:
        score += 2
    elif tier in {"medium", "m", "mid"}:
        score += 1
    elif tier in {"low", "l"}:
        score += 0
    else:
        score -= 1

    ctype = content_type.strip().lower()
    if ctype in {"tutorial", "education", "educational", "course"}:
        score += 1

    intent = engagement_intent.strip().lower()
    if intent in {"learn", "study", "deep_dive", "tutorial"}:
        score += 1

    if duration_seconds <= 0:
        score -= 2
    elif duration_seconds < 60:
        score -= 1
    elif duration_seconds > 3 * 60 * 60:
        score -= 1

    return max(1, min(10, score))
