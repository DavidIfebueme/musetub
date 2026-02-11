import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.db.models import AICache
from app.platform.redis import get_redis
from app.platform.services.inference import is_configured, text_completion


def pricing_explanation_cache_key(metadata: dict, suggested_price_per_second: int, quality_score: int) -> str:
    raw = json.dumps(
        {
            "metadata": metadata,
            "suggested_price_per_second": suggested_price_per_second,
            "quality_score": quality_score,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"pricing_explanation:{digest}"


def negotiation_summary_cache_key(
    *,
    creator_id: str,
    proposed_price_per_second: int,
    duration_seconds: int,
    accepted: bool,
    counter_price_per_second: int,
) -> str:
    raw = json.dumps(
        {
            "creator_id": creator_id,
            "proposed_price_per_second": proposed_price_per_second,
            "duration_seconds": duration_seconds,
            "accepted": accepted,
            "counter_price_per_second": counter_price_per_second,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"negotiation_summary:{digest}"


async def _cache_get(cache_key: str) -> str | None:
    try:
        redis = get_redis()
        cached = await redis.get(cache_key)
        if isinstance(cached, str) and cached:
            return cached
    except Exception:
        pass
    return None


async def _cache_set(cache_key: str, value: str) -> None:
    try:
        redis = get_redis()
        await redis.set(cache_key, value, ex=60 * 60 * 24 * 30)
    except Exception:
        pass


async def get_or_create_pricing_explanation(
    *,
    session: AsyncSession,
    metadata: dict,
    suggested_price_per_second: int,
    quality_score: int,
) -> str:
    cache_key = pricing_explanation_cache_key(metadata, suggested_price_per_second, quality_score)

    cached = await _cache_get(cache_key)
    if cached:
        return cached

    existing = await session.execute(select(AICache).where(AICache.cache_key == cache_key))
    row = existing.scalar_one_or_none()
    if row is not None:
        await _cache_set(cache_key, row.value_text)
        return row.value_text

    text = await _generate_pricing_explanation(
        metadata=metadata,
        suggested_price_per_second=suggested_price_per_second,
        quality_score=quality_score,
    )

    session.add(AICache(cache_key=cache_key, value_text=text))
    await session.commit()

    await _cache_set(cache_key, text)

    return text


async def get_or_create_negotiation_summary(
    *,
    session: AsyncSession,
    creator_id: str,
    proposed_price_per_second: int,
    duration_seconds: int,
    accepted: bool,
    counter_price_per_second: int,
) -> str:
    cache_key = negotiation_summary_cache_key(
        creator_id=creator_id,
        proposed_price_per_second=proposed_price_per_second,
        duration_seconds=duration_seconds,
        accepted=accepted,
        counter_price_per_second=counter_price_per_second,
    )

    cached = await _cache_get(cache_key)
    if cached:
        return cached

    existing = await session.execute(select(AICache).where(AICache.cache_key == cache_key))
    row = existing.scalar_one_or_none()
    if row is not None:
        await _cache_set(cache_key, row.value_text)
        return row.value_text

    text = await _generate_negotiation_summary(
        creator_id=creator_id,
        proposed_price_per_second=proposed_price_per_second,
        duration_seconds=duration_seconds,
        accepted=accepted,
        counter_price_per_second=counter_price_per_second,
    )

    session.add(AICache(cache_key=cache_key, value_text=text))
    await session.commit()

    await _cache_set(cache_key, text)

    return text


async def _generate_pricing_explanation(*, metadata: dict, suggested_price_per_second: int, quality_score: int) -> str:
    if not is_configured():
        return _fallback_explanation(metadata, suggested_price_per_second, quality_score)

    context = json.dumps(
        {"metadata": metadata, "quality_score": quality_score, "suggested_price_per_second": suggested_price_per_second},
        separators=(",", ":"),
    )

    try:
        response = await text_completion(
            system_prompt=(
                "You explain content pricing decisions on a video streaming platform. "
                "Be specific to the provided metadata. Keep responses to 1-2 sentences."
            ),
            user_prompt=f"Explain why this content has the suggested price per second.\n{context}",
            max_tokens=256,
        )
        if response.text:
            return response.text
    except Exception:
        pass

    return _fallback_explanation(metadata, suggested_price_per_second, quality_score)


async def _generate_negotiation_summary(
    *,
    creator_id: str,
    proposed_price_per_second: int,
    duration_seconds: int,
    accepted: bool,
    counter_price_per_second: int,
) -> str:
    if not is_configured():
        return _fallback_negotiation_summary(
            proposed_price_per_second=proposed_price_per_second,
            duration_seconds=duration_seconds,
            accepted=accepted,
            counter_price_per_second=counter_price_per_second,
        )

    context = json.dumps(
        {
            "proposed_price_per_second": proposed_price_per_second,
            "duration_seconds": duration_seconds,
            "accepted": accepted,
            "counter_price_per_second": counter_price_per_second,
        },
        separators=(",", ":"),
    )

    try:
        response = await text_completion(
            system_prompt=(
                "You write concise negotiation summaries for a video streaming platform. "
                "Keep responses to 1 sentence, neutral tone."
            ),
            user_prompt=f"Write a negotiation summary.\n{context}",
            max_tokens=128,
        )
        if response.text:
            return response.text[:200]
    except Exception:
        pass

    return _fallback_negotiation_summary(
        proposed_price_per_second=proposed_price_per_second,
        duration_seconds=duration_seconds,
        accepted=accepted,
        counter_price_per_second=counter_price_per_second,
    )


def _fallback_explanation(metadata: dict, suggested_price_per_second: int, quality_score: int) -> str:
    content_type = str(metadata.get("content_type") or "")
    resolution = str(metadata.get("resolution") or "")
    bitrate_tier = str(metadata.get("bitrate_tier") or "")
    duration = metadata.get("duration_seconds")
    return (
        f"Suggested rate is {suggested_price_per_second} (USDC minor units/sec) based on "
        f"quality score {quality_score} for a {content_type} at {resolution} ({bitrate_tier}), duration {duration}s."
    )


def _fallback_negotiation_summary(
    *,
    proposed_price_per_second: int,
    duration_seconds: int,
    accepted: bool,
    counter_price_per_second: int,
) -> str:
    if accepted:
        return f"Accepted {proposed_price_per_second} (minor units/sec) for {duration_seconds}s."
    return (
        f"Proposal {proposed_price_per_second} (minor units/sec) for {duration_seconds}s isn't within policy; "
        f"counter is {counter_price_per_second} (minor units/sec)."
    )
