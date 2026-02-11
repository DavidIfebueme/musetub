from unittest.mock import AsyncMock, patch

import pytest

from app.features.ai_agents.services.negotiation import (
    evaluate_price_proposal,
    negotiate_with_reasoning,
)


def test_negotiation_accepts_within_effective_range_no_tiers():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=150,
        duration_seconds=30,
    )
    assert decision.accepted is True
    assert decision.counter_price_per_second == 150
    assert decision.reasoning == ""


def test_negotiation_counters_below_min():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=20,
        duration_seconds=30,
    )
    assert decision.accepted is False
    assert decision.counter_price_per_second == 100


def test_negotiation_applies_best_discount_tier():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={
            "tiers": [
                {"min_seconds": 0, "discount_bps": 0},
                {"min_seconds": 600, "discount_bps": 500},
                {"min_seconds": 3600, "discount_bps": 2000},
            ]
        },
        proposed_price_per_second=90,
        duration_seconds=3600,
    )

    assert decision.discount_bps == 2000
    assert decision.effective_min_price_per_second == 80
    assert decision.effective_max_price_per_second == 160
    assert decision.accepted is True
    assert decision.counter_price_per_second == 90


def test_negotiation_counters_above_max():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=500,
        duration_seconds=30,
    )
    assert decision.accepted is False
    assert decision.counter_price_per_second == 200


def test_negotiation_boundary_min():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=100,
        duration_seconds=30,
    )
    assert decision.accepted is True


def test_negotiation_boundary_max():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=200,
        duration_seconds=30,
    )
    assert decision.accepted is True


def test_negotiation_negative_min_clamped():
    decision = evaluate_price_proposal(
        min_price_per_second=-50,
        max_price_per_second=100,
        bulk_tiers_json={},
        proposed_price_per_second=0,
        duration_seconds=30,
    )
    assert decision.accepted is True
    assert decision.effective_min_price_per_second == 0


@pytest.mark.asyncio
async def test_negotiate_with_reasoning_not_configured():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=150,
        duration_seconds=60,
    )

    with patch("app.features.ai_agents.services.negotiation.is_configured", return_value=False):
        result = await negotiate_with_reasoning(
            decision=decision,
            content_quality_score=7,
            content_type="tutorial",
            proposed_price_per_second=150,
            duration_seconds=60,
        )

    assert result.accepted == decision.accepted
    assert result.counter_price_per_second == decision.counter_price_per_second
    assert result.reasoning == ""


@pytest.mark.asyncio
async def test_negotiate_with_reasoning_llm_response():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=120,
        duration_seconds=300,
    )

    mock_response = AsyncMock()
    mock_response.text = '{"counter": 140, "reasoning": "Fair price for high quality tutorial content."}'

    with patch("app.features.ai_agents.services.negotiation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.negotiation.text_completion", return_value=mock_response):
        result = await negotiate_with_reasoning(
            decision=decision,
            content_quality_score=8,
            content_type="tutorial",
            proposed_price_per_second=120,
            duration_seconds=300,
        )

    assert result.accepted is True
    assert result.counter_price_per_second == 140
    assert "tutorial" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_negotiate_with_reasoning_clamps_counter():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=50,
        duration_seconds=30,
    )

    mock_response = AsyncMock()
    mock_response.text = '{"counter": 999, "reasoning": "Overpriced suggestion"}'

    with patch("app.features.ai_agents.services.negotiation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.negotiation.text_completion", return_value=mock_response):
        result = await negotiate_with_reasoning(
            decision=decision,
            content_quality_score=5,
            content_type="music",
            proposed_price_per_second=50,
            duration_seconds=30,
        )

    assert result.counter_price_per_second == 200
    assert result.accepted is False


@pytest.mark.asyncio
async def test_negotiate_with_reasoning_llm_exception():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=150,
        duration_seconds=60,
    )

    with patch("app.features.ai_agents.services.negotiation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.negotiation.text_completion", side_effect=Exception("timeout")):
        result = await negotiate_with_reasoning(
            decision=decision,
            content_quality_score=7,
            content_type="tutorial",
            proposed_price_per_second=150,
            duration_seconds=60,
        )

    assert result.accepted == decision.accepted
    assert result.counter_price_per_second == decision.counter_price_per_second


@pytest.mark.asyncio
async def test_negotiate_with_reasoning_invalid_json():
    decision = evaluate_price_proposal(
        min_price_per_second=100,
        max_price_per_second=200,
        bulk_tiers_json={},
        proposed_price_per_second=150,
        duration_seconds=60,
    )

    mock_response = AsyncMock()
    mock_response.text = "not valid json"

    with patch("app.features.ai_agents.services.negotiation.is_configured", return_value=True), \
         patch("app.features.ai_agents.services.negotiation.text_completion", return_value=mock_response):
        result = await negotiate_with_reasoning(
            decision=decision,
            content_quality_score=7,
            content_type="tutorial",
            proposed_price_per_second=150,
            duration_seconds=60,
        )

    assert result.accepted == decision.accepted
    assert result.counter_price_per_second == decision.counter_price_per_second
