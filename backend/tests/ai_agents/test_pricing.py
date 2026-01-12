from app.features.ai_agents.services.pricing import compute_suggested_price_per_second_minor_units


def test_pricing_floor_and_ceiling_enforced():
    assert compute_suggested_price_per_second_minor_units(quality_score=-10) == 5
    assert compute_suggested_price_per_second_minor_units(quality_score=1) >= 5
    assert compute_suggested_price_per_second_minor_units(quality_score=999) == 2000


def test_pricing_monotonic_in_quality():
    low = compute_suggested_price_per_second_minor_units(quality_score=2)
    high = compute_suggested_price_per_second_minor_units(quality_score=9)
    assert high > low
