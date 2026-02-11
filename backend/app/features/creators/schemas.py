from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreatorSettlementItem(BaseModel):
    id: str
    content_id: str
    channel_id: str
    amount_gross: int
    amount_creator: int
    tx_hash: str
    created_at: datetime


class CreatorContentEarningsItem(BaseModel):
    content_id: str
    title: str
    amount_gross: int
    amount_creator: int


class CreatorDashboardResponse(BaseModel):
    total_amount_gross: int
    total_amount_creator: int
    withdrawable_balance: int | None
    content_count: int
    platform_fee_bps: int
    earnings_by_content: list[CreatorContentEarningsItem]
    recent_settlements: list[CreatorSettlementItem]


class WithdrawResponse(BaseModel):
    tx_id: str
