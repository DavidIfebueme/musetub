def compute_quality_score(
    *,
    duration_seconds: int,
    resolution: str,
    bitrate_tier: str,
    content_type: str,
    engagement_intent: str,
) -> int:
    score = 4

    res = resolution.strip().lower().replace(" ", "")
    if res in {"2160p", "4k"}:
        score += 6
    elif res == "1440p":
        score += 5
    elif res == "1080p":
        score += 4
    elif res == "720p":
        score += 2
    elif res == "480p":
        score += 0
    else:
        score -= 1

    tier = bitrate_tier.strip().lower()
    if tier in {"high", "h"}:
        score += 2
    elif tier in {"medium", "m", "mid"}:
        score += 1
    elif tier in {"low", "l"}:
        score += 0
    else:
        score -= 1

    ctype = content_type.strip().lower()
    if ctype in {"tutorial", "education", "educational", "course"}:
        score += 1
    elif ctype in {"podcast", "music"}:
        score += 0
    else:
        score += 0

    intent = engagement_intent.strip().lower()
    if intent in {"learn", "study", "deep_dive", "tutorial"}:
        score += 1

    if duration_seconds <= 0:
        score -= 2
    elif duration_seconds < 60:
        score -= 1
    elif duration_seconds > 3 * 60 * 60:
        score -= 1

    if score < 1:
        return 1
    if score > 10:
        return 10
    return score
