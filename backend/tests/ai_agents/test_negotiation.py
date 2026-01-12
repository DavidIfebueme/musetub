from app.features.ai_agents.services.negotiation import evaluate_price_proposal


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
