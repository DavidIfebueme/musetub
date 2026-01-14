from datetime import datetime

from pydantic import BaseModel


class ChannelOpenRequest(BaseModel):
    content_id: str


class ChannelTickRequest(BaseModel):
    channel_id: str


class ChannelCloseRequest(BaseModel):
    channel_id: str


class ChannelResponse(BaseModel):
    id: str
    user_id: str
    content_id: str
    status: str

    price_per_second_locked: int
    total_seconds_streamed: int
    total_amount_owed: int
    total_amount_settled: int

    last_tick_at: datetime | None
    last_settlement_at: datetime | None
    opened_at: datetime
    closed_at: datetime | None

    escrow_address: str | None
    usdc_address: str | None


class TickResponse(ChannelResponse):
    tick_seconds: int
    did_settle: bool
    settlement_tx_id: str | None
    settlement_amount: int | None
