from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserHistoryItem(BaseModel):
    channel_id: str
    content_id: str
    content_title: str
    creator_id: str
    status: str
    price_per_second_locked: int
    total_seconds_streamed: int
    total_amount_owed: int
    total_amount_settled: int
    last_tick_at: datetime | None
    last_settlement_at: datetime | None
    opened_at: datetime
    closed_at: datetime | None


class UserSpendingResponse(BaseModel):
    total_seconds_streamed: int
    total_amount_owed: int
    total_amount_settled: int
