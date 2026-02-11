from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.features.ai_agents.services.content_analysis import (
    ContentAnalysisResult,
    analyze_upload,
)
from app.features.ai_agents.services.moderation import ModerationResult
from app.platform.services.video_analysis import VideoMetadata


def _mock_metadata(
    *,
    height=1080,
    width=1920,
    bitrate=5_000_000,
    codec="h264",
    framerate=30.0,
    duration=120.0,
) -> VideoMetadata:
    return VideoMetadata(
        duration_seconds=duration,
        width=width,
        height=height,
        bitrate=bitrate,
        codec=codec,
        framerate=framerate,
        has_video=True,
        has_audio=True,
    )


@pytest.mark.asyncio
async def test_analyze_upload_with_ffprobe_and_inference():
    metadata = _mock_metadata()

    mock_vision_response = AsyncMock()
    mock_vision_response.text = '{"visual_score": 8.0, "content_score": 7.0, "summary": "High quality content"}'

    mock_mod_result = ModerationResult(safe=True, flags=[], confidence=0.9, reason="")

    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", return_value=metadata), \
         patch("app.features.ai_agents.services.content_analysis.extract_keyframes", return_value=[b"frame1", b"frame2"]), \
         patch("app.features.ai_agents.services.content_analysis.frames_to_base64", return_value=["b64_1", "b64_2"]), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.content_analysis.vision_analysis", return_value=mock_vision_response), \
         patch("app.features.ai_agents.services.content_analysis.moderate_content", return_value=mock_mod_result):

        result = await analyze_upload(
            file_bytes=b"fake video data",
            filename="test.mp4",
            content_type="tutorial",
            engagement_intent="learn",
        )

    assert isinstance(result, ContentAnalysisResult)
    assert result.duration_seconds == 120
    assert result.resolution == "1080p"
    assert result.bitrate_tier == "medium"
    assert result.moderation_safe is True
    assert 1 <= result.quality_score <= 10
    assert result.suggested_price > 0
    assert result.analysis_summary == "High quality content"


@pytest.mark.asyncio
async def test_analyze_upload_ffprobe_only_no_inference():
    metadata = _mock_metadata(height=2160, width=3840, bitrate=15_000_000, codec="hevc", framerate=60.0)

    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", return_value=metadata), \
         patch("app.features.ai_agents.services.content_analysis.extract_keyframes", return_value=[]), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=False):

        result = await analyze_upload(
            file_bytes=b"fake video data",
            filename="test.mp4",
            content_type="tutorial",
            engagement_intent="learn",
        )

    assert result.duration_seconds == 120
    assert result.resolution == "2160p"
    assert result.bitrate_tier == "high"
    assert result.moderation_safe is True
    assert 1 <= result.quality_score <= 10


@pytest.mark.asyncio
async def test_analyze_upload_fallback_to_heuristic():
    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", side_effect=RuntimeError("no ffprobe")), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=False):

        result = await analyze_upload(
            file_bytes=b"some data",
            filename="test.mp4",
            content_type="tutorial",
            engagement_intent="learn",
            form_duration=120,
            form_resolution="1080p",
            form_bitrate_tier="high",
        )

    assert result.duration_seconds == 120
    assert result.resolution == "1080p"
    assert result.bitrate_tier == "high"
    assert result.moderation_safe is True
    assert 1 <= result.quality_score <= 10


@pytest.mark.asyncio
async def test_analyze_upload_fallback_defaults_when_no_form_data():
    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", side_effect=RuntimeError("fail")), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=False):

        result = await analyze_upload(
            file_bytes=b"some data",
            filename="test.mp4",
            content_type="other",
            engagement_intent="casual",
        )

    assert result.duration_seconds == 0
    assert result.resolution == "unknown"
    assert result.bitrate_tier == "low"
    assert result.quality_score >= 1


@pytest.mark.asyncio
async def test_analyze_upload_moderation_flags_content():
    metadata = _mock_metadata()

    mock_vision_response = AsyncMock()
    mock_vision_response.text = '{"visual_score": 5.0, "content_score": 5.0, "summary": "Normal"}'

    mock_mod_result = ModerationResult(
        safe=False, flags=["violence"], confidence=0.92, reason="Graphic content detected"
    )

    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", return_value=metadata), \
         patch("app.features.ai_agents.services.content_analysis.extract_keyframes", return_value=[b"frame1"]), \
         patch("app.features.ai_agents.services.content_analysis.frames_to_base64", return_value=["b64_1"]), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.content_analysis.vision_analysis", return_value=mock_vision_response), \
         patch("app.features.ai_agents.services.content_analysis.moderate_content", return_value=mock_mod_result):

        result = await analyze_upload(
            file_bytes=b"fake video data",
            filename="test.mp4",
            content_type="other",
            engagement_intent="casual",
        )

    assert result.moderation_safe is False
    assert result.moderation_reason == "Graphic content detected"


@pytest.mark.asyncio
async def test_analyze_upload_text_analysis_exception_graceful():
    metadata = _mock_metadata()

    mock_mod_result = ModerationResult(safe=True, flags=[], confidence=0.0, reason="")

    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", return_value=metadata), \
         patch("app.features.ai_agents.services.content_analysis.extract_keyframes", return_value=[b"frame1"]), \
         patch("app.features.ai_agents.services.content_analysis.frames_to_base64", return_value=["b64_1"]), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.content_analysis.vision_analysis", side_effect=Exception("API down")), \
         patch("app.features.ai_agents.services.content_analysis.moderate_content", return_value=mock_mod_result):

        result = await analyze_upload(
            file_bytes=b"fake video data",
            filename="test.mp4",
            content_type="tutorial",
            engagement_intent="learn",
        )

    assert 1 <= result.quality_score <= 10
    assert result.moderation_safe is True


@pytest.mark.asyncio
async def test_analyze_upload_audio_only():
    audio_metadata = VideoMetadata(
        duration_seconds=180.0, width=0, height=0,
        bitrate=320_000, codec="mp3", framerate=0.0,
        has_video=False, has_audio=True,
    )

    mock_mod_result = ModerationResult(safe=True, flags=[], confidence=0.0, reason="")

    with patch("app.features.ai_agents.services.content_analysis.extract_metadata", return_value=audio_metadata), \
         patch("app.features.ai_agents.services.content_analysis.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.content_analysis.text_completion", side_effect=Exception("skip")), \
         patch("app.features.ai_agents.services.content_analysis.moderate_content", return_value=mock_mod_result):

        result = await analyze_upload(
            file_bytes=b"audio data",
            filename="podcast.mp3",
            content_type="podcast",
            engagement_intent="learn",
        )

    assert result.duration_seconds == 180
    assert result.resolution == "unknown"
    assert result.moderation_safe is True
    assert 1 <= result.quality_score <= 10
