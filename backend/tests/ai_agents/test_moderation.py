from unittest.mock import AsyncMock, patch

import pytest

from app.features.ai_agents.services.moderation import ModerationResult, moderate_content


@pytest.mark.asyncio
async def test_moderate_content_not_configured():
    with patch("app.features.ai_agents.services.moderation.is_configured", return_value=False):
        result = await moderate_content(
            filename="test.mp4",
            content_type="tutorial",
            duration_seconds=120,
            resolution="1080p",
        )

    assert result.safe is True
    assert result.reason == "Moderation not configured"


@pytest.mark.asyncio
async def test_moderate_content_safe_response():
    mock_response = AsyncMock()
    mock_response.text = '{"safe": true, "flags": [], "confidence": 0.95, "reason": "Content is clean"}'

    with patch("app.features.ai_agents.services.moderation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.moderation.text_completion", return_value=mock_response):
        result = await moderate_content(
            filename="test.mp4",
            content_type="tutorial",
            duration_seconds=120,
            resolution="1080p",
        )

    assert isinstance(result, ModerationResult)
    assert result.safe is True
    assert result.flags == []
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_moderate_content_unsafe_response():
    mock_response = AsyncMock()
    mock_response.text = '{"safe": false, "flags": ["violence", "gore"], "confidence": 0.88, "reason": "Graphic violence detected"}'

    with patch("app.features.ai_agents.services.moderation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.moderation.text_completion", return_value=mock_response):
        result = await moderate_content(
            filename="test.mp4",
            content_type="other",
            duration_seconds=60,
            resolution="720p",
        )

    assert result.safe is False
    assert "violence" in result.flags
    assert "gore" in result.flags
    assert result.confidence == 0.88
    assert "violence" in result.reason.lower()


@pytest.mark.asyncio
async def test_moderate_content_invalid_json():
    mock_response = AsyncMock()
    mock_response.text = "not valid json"

    with patch("app.features.ai_agents.services.moderation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.moderation.text_completion", return_value=mock_response):
        result = await moderate_content(
            filename="test.mp4",
            content_type="other",
            duration_seconds=60,
            resolution="720p",
        )

    assert result.safe is True
    assert result.reason == "Moderation unavailable"


@pytest.mark.asyncio
async def test_moderate_content_api_exception():
    with patch("app.features.ai_agents.services.moderation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.moderation.text_completion", side_effect=Exception("API error")):
        result = await moderate_content(
            filename="test.mp4",
            content_type="other",
            duration_seconds=60,
            resolution="720p",
        )

    assert result.safe is True
    assert result.reason == "Moderation unavailable"


@pytest.mark.asyncio
async def test_moderate_content_partial_json():
    mock_response = AsyncMock()
    mock_response.text = '{"safe": false}'

    with patch("app.features.ai_agents.services.moderation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.moderation.text_completion", return_value=mock_response):
        result = await moderate_content(
            filename="test.mp4",
            content_type="other",
            duration_seconds=60,
            resolution="720p",
        )

    assert result.safe is False
    assert result.flags == []
    assert result.confidence == 0.0
    assert result.reason == ""
