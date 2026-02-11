from app.features.ai_agents.services.quality import (
    QualityResult,
    build_quality_result,
    compute_composite_score,
    compute_quality_score,
    compute_technical_score,
    parse_llm_scores,
)
from app.platform.services.video_analysis import VideoMetadata


def _make_metadata(
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


def test_technical_score_4k_hevc_60fps():
    m = _make_metadata(height=2160, width=3840, bitrate=20_000_000, codec="hevc", framerate=60.0)
    score = compute_technical_score(m)
    assert score == 10.0


def test_technical_score_1080p_h264_30fps():
    m = _make_metadata(height=1080, width=1920, bitrate=5_000_000, codec="h264", framerate=30.0)
    score = compute_technical_score(m)
    assert score == 7.0


def test_technical_score_720p_low_bitrate():
    m = _make_metadata(height=720, width=1280, bitrate=800_000, codec="h264", framerate=24.0)
    score = compute_technical_score(m)
    assert 3.0 <= score <= 5.0


def test_technical_score_480p_unknown_codec():
    m = _make_metadata(height=480, width=854, bitrate=500_000, codec="unknown", framerate=15.0)
    score = compute_technical_score(m)
    assert 1.0 <= score <= 4.0


def test_technical_score_capped_at_10():
    m = _make_metadata(height=4320, width=7680, bitrate=100_000_000, codec="av1", framerate=120.0)
    score = compute_technical_score(m)
    assert score <= 10.0


def test_technical_score_modern_codecs_bonus():
    m_h264 = _make_metadata(codec="h264")
    m_av1 = _make_metadata(codec="av1")
    assert compute_technical_score(m_av1) > compute_technical_score(m_h264)


def test_parse_llm_scores_valid_json():
    raw = '{"visual_score": 8.5, "content_score": 7.0, "summary": "High quality tutorial"}'
    visual, content, summary = parse_llm_scores(raw)
    assert visual == 8.5
    assert content == 7.0
    assert summary == "High quality tutorial"


def test_parse_llm_scores_clamped():
    raw = '{"visual_score": 15.0, "content_score": -3.0, "summary": "test"}'
    visual, content, summary = parse_llm_scores(raw)
    assert visual == 10.0
    assert content == 0.0


def test_parse_llm_scores_invalid_json():
    visual, content, summary = parse_llm_scores("not json at all")
    assert visual == 5.0
    assert content == 5.0
    assert summary == "Analysis unavailable"


def test_parse_llm_scores_missing_fields():
    raw = '{"visual_score": 6.0}'
    visual, content, summary = parse_llm_scores(raw)
    assert visual == 6.0
    assert content == 5.0
    assert summary == ""


def test_parse_llm_scores_none_input():
    visual, content, summary = parse_llm_scores(None)
    assert visual == 5.0
    assert content == 5.0


def test_composite_score_weighted():
    score = compute_composite_score(
        technical_score=10.0,
        visual_score=10.0,
        content_score=10.0,
    )
    assert score == 10


def test_composite_score_all_zeros():
    score = compute_composite_score(
        technical_score=0.0,
        visual_score=0.0,
        content_score=0.0,
    )
    assert score == 1


def test_composite_score_mixed():
    score = compute_composite_score(
        technical_score=8.0,
        visual_score=6.0,
        content_score=4.0,
    )
    expected = round((8.0 * 0.3) + (6.0 * 0.5) + (4.0 * 0.2))
    assert score == expected


def test_composite_score_technical_heavy():
    score = compute_composite_score(
        technical_score=10.0,
        visual_score=5.0,
        content_score=5.0,
    )
    assert 5 <= score <= 7


def test_build_quality_result():
    result = build_quality_result(
        technical_score=8.0,
        visual_score=7.0,
        content_score=6.0,
        summary="Good quality",
    )
    assert isinstance(result, QualityResult)
    assert result.technical_score == 8.0
    assert result.visual_score == 7.0
    assert result.content_score == 6.0
    assert result.summary == "Good quality"
    assert 1 <= result.score <= 10


def test_quality_score_clamped_range():
    score = compute_quality_score(
        duration_seconds=60,
        resolution="4k",
        bitrate_tier="high",
        content_type="tutorial",
        engagement_intent="learn",
    )
    assert 1 <= score <= 10


def test_quality_score_low_values_dont_underflow():
    score = compute_quality_score(
        duration_seconds=-1,
        resolution="unknown",
        bitrate_tier="unknown",
        content_type="other",
        engagement_intent="",
    )
    assert score == 1


def test_quality_score_max_score():
    score = compute_quality_score(
        duration_seconds=300,
        resolution="4k",
        bitrate_tier="high",
        content_type="tutorial",
        engagement_intent="learn",
    )
    assert score == 10
