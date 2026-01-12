from app.features.ai_agents.services.quality import compute_quality_score


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
