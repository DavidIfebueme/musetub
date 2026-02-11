import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.platform.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False)

    wallet_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    circle_wallet_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CreatorPolicy(Base):
    __tablename__ = "creator_policies"

    creator_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    min_price_per_second: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_price_per_second: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bulk_tiers_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class Content(Base):
    __tablename__ = "content"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(64))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    resolution: Mapped[str] = mapped_column(String(32))
    bitrate_tier: Mapped[str] = mapped_column(String(32))
    engagement_intent: Mapped[str] = mapped_column(String(64))

    quality_score: Mapped[int] = mapped_column(Integer)
    suggested_price_per_second: Mapped[int] = mapped_column(BigInteger)
    price_per_second: Mapped[int] = mapped_column(BigInteger)
    ipfs_cid: Mapped[str] = mapped_column(String(128))
    thumbnail_cid: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StreamCredit(Base):
    __tablename__ = "stream_credits"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="uq_stream_credits_user_content"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("content.id", ondelete="CASCADE"), index=True)

    seconds_remaining: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentChannel(Base):
    __tablename__ = "payment_channels"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("content.id", ondelete="CASCADE"), index=True)

    price_per_second_locked: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'active'"))

    total_seconds_streamed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_amount_owed: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    total_amount_settled: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))

    last_tick_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_settlement_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    opened_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("payment_channels.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AICache(Base):
    __tablename__ = "ai_cache"

    cache_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
