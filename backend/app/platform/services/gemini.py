import hashlib
import json

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.config import settings
from app.platform.db.models import AICache
from app.platform.redis import get_redis


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


async def get_or_create_pricing_explanation(
    *,
    session: AsyncSession,
    metadata: dict,
    suggested_price_per_second: int,
    quality_score: int,
) -> str:
    cache_key = pricing_explanation_cache_key(metadata, suggested_price_per_second, quality_score)

    redis = None
    try:
        redis = get_redis()
        cached = await redis.get(cache_key)
        if isinstance(cached, str) and cached:
            return cached
    except Exception:
        redis = None

    existing = await session.execute(select(AICache).where(AICache.cache_key == cache_key))
    row = existing.scalar_one_or_none()
    if row is not None:
        if redis is not None:
            try:
                await redis.set(cache_key, row.value_text, ex=60 * 60 * 24 * 30)
            except Exception:
                pass
        return row.value_text

    text = await _generate_pricing_explanation(
        metadata=metadata,
        suggested_price_per_second=suggested_price_per_second,
        quality_score=quality_score,
    )

    session.add(AICache(cache_key=cache_key, value_text=text))
    await session.commit()

    if redis is not None:
        try:
            await redis.set(cache_key, text, ex=60 * 60 * 24 * 30)
        except Exception:
            pass

    return text


async def _generate_pricing_explanation(*, metadata: dict, suggested_price_per_second: int, quality_score: int) -> str:
    if not settings.gemini_api_key:
        return _fallback_explanation(metadata, suggested_price_per_second, quality_score)

    model = settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    prompt = (
        "Explain in 1-2 sentences why this content has the suggested price per second. "
        "Be specific to the provided metadata."
    )

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"text": json.dumps(metadata, separators=(",", ":"))},
                    {"text": f"quality_score={quality_score}"},
                    {"text": f"suggested_price_per_second={suggested_price_per_second}"},
                ],
            }
        ]
    }

    timeout = httpx.Timeout(settings.gemini_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, params={"key": settings.gemini_api_key}, json=body)

    if resp.status_code >= 400:
        return _fallback_explanation(metadata, suggested_price_per_second, quality_score)

    try:
        payload = resp.json()
        candidates = payload.get("candidates")
        if isinstance(candidates, list) and candidates:
            content = candidates[0].get("content")
            if isinstance(content, dict):
                parts = content.get("parts")
                if isinstance(parts, list) and parts:
                    text = parts[0].get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
    except Exception:
        pass

    return _fallback_explanation(metadata, suggested_price_per_second, quality_score)


def _fallback_explanation(metadata: dict, suggested_price_per_second: int, quality_score: int) -> str:
    content_type = str(metadata.get("content_type") or "")
    resolution = str(metadata.get("resolution") or "")
    bitrate_tier = str(metadata.get("bitrate_tier") or "")
    duration = metadata.get("duration_seconds")
    return (
        f"Suggested rate is {suggested_price_per_second} (USDC minor units/sec) based on "
        f"quality score {quality_score} for a {content_type} at {resolution} ({bitrate_tier}), duration {duration}s."
    )
