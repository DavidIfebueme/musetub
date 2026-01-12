from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.db.models import CreatorPolicy


@dataclass(frozen=True)
class NegotiationDecision:
    accepted: bool
    counter_price_per_second: int
    discount_bps: int
    effective_min_price_per_second: int
    effective_max_price_per_second: int


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _pick_discount_bps(*, bulk_tiers_json: dict, duration_seconds: int) -> int:
    tiers = bulk_tiers_json.get("tiers")
    if not isinstance(tiers, list) or not tiers:
        return 0

    best_discount = 0
    for tier in tiers:
        if not isinstance(tier, dict):
            continue
        min_seconds = tier.get("min_seconds")
        discount_bps = tier.get("discount_bps")
        if not isinstance(min_seconds, int) or not isinstance(discount_bps, int):
            continue
        if duration_seconds >= min_seconds and discount_bps > best_discount:
            best_discount = discount_bps

    if best_discount < 0:
        return 0
    if best_discount > 9000:
        return 9000
    return best_discount


def evaluate_price_proposal(
    *,
    min_price_per_second: int,
    max_price_per_second: int,
    bulk_tiers_json: dict,
    proposed_price_per_second: int,
    duration_seconds: int,
) -> NegotiationDecision:
    if min_price_per_second < 0:
        min_price_per_second = 0
    if max_price_per_second < min_price_per_second:
        max_price_per_second = min_price_per_second

    if duration_seconds < 0:
        duration_seconds = 0

    discount_bps = _pick_discount_bps(bulk_tiers_json=bulk_tiers_json or {}, duration_seconds=duration_seconds)
    multiplier_bps = 10000 - discount_bps

    effective_min = (min_price_per_second * multiplier_bps) // 10000
    effective_max = (max_price_per_second * multiplier_bps) // 10000

    if effective_max < effective_min:
        effective_max = effective_min

    accepted = effective_min <= proposed_price_per_second <= effective_max
    counter = _clamp_int(proposed_price_per_second, effective_min, effective_max)

    return NegotiationDecision(
        accepted=accepted,
        counter_price_per_second=counter,
        discount_bps=discount_bps,
        effective_min_price_per_second=effective_min,
        effective_max_price_per_second=effective_max,
    )


async def get_creator_policy(
    *,
    session: AsyncSession,
    creator_id: str,
) -> CreatorPolicy | None:
    result = await session.execute(select(CreatorPolicy).where(CreatorPolicy.creator_id == creator_id))
    return result.scalar_one_or_none()


def evaluate_price_proposal_with_policy(
    *,
    policy: CreatorPolicy | None,
    proposed_price_per_second: int,
    duration_seconds: int,
    default_min_price_per_second: int = 5,
    default_max_price_per_second: int = 2000,
) -> NegotiationDecision:
    if policy is None:
        return evaluate_price_proposal(
            min_price_per_second=default_min_price_per_second,
            max_price_per_second=default_max_price_per_second,
            bulk_tiers_json={},
            proposed_price_per_second=proposed_price_per_second,
            duration_seconds=duration_seconds,
        )

    return evaluate_price_proposal(
        min_price_per_second=int(policy.min_price_per_second),
        max_price_per_second=int(policy.max_price_per_second),
        bulk_tiers_json=policy.bulk_tiers_json or {},
        proposed_price_per_second=proposed_price_per_second,
        duration_seconds=duration_seconds,
    )
