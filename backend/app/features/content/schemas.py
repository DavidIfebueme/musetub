from datetime import datetime

from pydantic import BaseModel


class ContentResponse(BaseModel):
    id: str
    creator_id: str
    title: str
    description: str
    content_type: str
    duration_seconds: int
    resolution: str
    bitrate_tier: str
    engagement_intent: str
    quality_score: int
    suggested_price_per_second: int
    price_per_second: int
    ipfs_cid: str
    playback_url: str
    pricing_explanation: str
    created_at: datetime


class ContentListItem(BaseModel):
    id: str
    creator_id: str
    title: str
    content_type: str
    duration_seconds: int
    price_per_second: int
    quality_score: int
    playback_url: str
    created_at: datetime
