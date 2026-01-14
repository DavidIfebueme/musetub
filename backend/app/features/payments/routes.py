from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.payments.schemas import (
    ChannelCloseRequest,
    ChannelOpenRequest,
    ChannelResponse,
    ChannelTickRequest,
    TickResponse,
)
from app.platform.config import settings
from app.platform.db.models import Content, PaymentChannel, Settlement, User
from app.platform.db.session import get_session
from app.platform.redis import get_redis
from app.platform.security.auth import get_current_user
from app.platform.services.chain import ChainClient
from app.platform.services.circle_wallets import CircleWalletsClient


router = APIRouter(prefix="/payments/channel")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_circle_wallets_client() -> CircleWalletsClient:
    return CircleWalletsClient()


def _channel_response(channel: PaymentChannel) -> ChannelResponse:
    return ChannelResponse(
        id=channel.id,
        user_id=channel.user_id,
        content_id=channel.content_id,
        status=channel.status,
        price_per_second_locked=channel.price_per_second_locked,
        total_seconds_streamed=channel.total_seconds_streamed,
        total_amount_owed=channel.total_amount_owed,
        total_amount_settled=channel.total_amount_settled,
        last_tick_at=channel.last_tick_at,
        last_settlement_at=channel.last_settlement_at,
        opened_at=channel.opened_at,
        closed_at=channel.closed_at,
        escrow_address=settings.escrow_address,
        usdc_address=settings.usdc_address,
    )


def _live_settlement_enabled() -> bool:
    return bool(
        settings.circle_api_key
        and settings.circle_entity_secret
        and settings.arc_rpc_url
        and settings.arc_chain_id is not None
        and settings.usdc_address
        and settings.escrow_address
    )


async def _try_acquire_tick_slot(channel_id: str, now: datetime) -> bool:
    slot = int(now.timestamp()) // 10
    key = f"tick:{channel_id}:{slot}"

    try:
        redis = get_redis()
        return bool(await redis.set(key, "1", ex=12, nx=True))
    except Exception:
        return True


async def _settle_unpaid_amount(
    *,
    session: AsyncSession,
    circle: CircleWalletsClient,
    channel: PaymentChannel,
    content: Content,
    viewer: User,
    creator: User,
    now: datetime,
    force: bool,
) -> tuple[bool, str | None, int | None]:
    if channel.status != "active":
        return False, None, None

    unpaid = int(channel.total_amount_owed - channel.total_amount_settled)
    if unpaid <= 0:
        return False, None, None

    if not force:
        if channel.last_settlement_at is not None:
            if now - channel.last_settlement_at < timedelta(seconds=120):
                return False, None, None
        else:
            if now - channel.opened_at < timedelta(seconds=120):
                return False, None, None

    tx_id: str
    if _live_settlement_enabled():
        if not viewer.circle_wallet_id or not viewer.wallet_address:
            raise HTTPException(status_code=400, detail="User wallet not available")
        if not creator.wallet_address:
            raise HTTPException(status_code=400, detail="Creator wallet not available")

        chain = ChainClient.from_settings()

        nonce = "0x" + secrets.token_hex(32)
        valid_after = int(now.timestamp()) - 5
        valid_before = int((now + timedelta(minutes=5)).timestamp())

        typed_data = chain.erc3009_receive_with_authorization_typed_data(
            from_address=viewer.wallet_address,
            to_address=chain.config.escrow_address,
            value=unpaid,
            valid_after=valid_after,
            valid_before=valid_before,
            nonce=nonce,
        )

        signature = await circle.sign_typed_data(
            wallet_id=viewer.circle_wallet_id,
            blockchain="ARC-TESTNET",
            typed_data=typed_data,
            memo=f"musetub:settle:{channel.id}",
        )

        tx_id = await circle.create_contract_execution_transaction(
            wallet_id=viewer.circle_wallet_id,
            blockchain="ARC-TESTNET",
            contract_address=chain.config.escrow_address,
            abi_function_signature="streamWithAuthorization(address,address,uint256,uint256,uint256,bytes32,bytes)",
            abi_parameters=[
                viewer.wallet_address,
                creator.wallet_address,
                unpaid,
                valid_after,
                valid_before,
                nonce,
                signature,
            ],
            ref_id=f"channel:{channel.id}",
        )
    else:
        tx_id = f"simulated:{uuid4()}"

    session.add(Settlement(channel_id=channel.id, amount=unpaid, tx_hash=tx_id))
    channel.total_amount_settled += unpaid
    channel.last_settlement_at = now

    return True, tx_id, unpaid


@router.post("/open", response_model=ChannelResponse)
async def open_channel(
    body: ChannelOpenRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChannelResponse:
    result = await session.execute(select(Content).where(Content.id == body.content_id))
    content = result.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Not found")

    channel = PaymentChannel(
        user_id=user.id,
        content_id=content.id,
        price_per_second_locked=content.price_per_second,
    )

    session.add(channel)
    await session.commit()
    await session.refresh(channel)

    return _channel_response(channel)


@router.post("/tick", response_model=TickResponse)
async def tick_channel(
    body: ChannelTickRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    circle: CircleWalletsClient = Depends(get_circle_wallets_client),
) -> TickResponse:
    now = _utcnow()

    result = await session.execute(
        select(PaymentChannel).where(PaymentChannel.id == body.channel_id, PaymentChannel.user_id == user.id).with_for_update()
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Not found")
    if channel.status != "active":
        raise HTTPException(status_code=400, detail="Channel is not active")

    ok = await _try_acquire_tick_slot(channel.id, now)
    if not ok:
        await session.refresh(channel)
        base = _channel_response(channel)
        return TickResponse(**base.model_dump(), tick_seconds=0, did_settle=False, settlement_tx_id=None, settlement_amount=None)

    tick_seconds = 10
    channel.total_seconds_streamed += tick_seconds
    channel.total_amount_owed += int(channel.price_per_second_locked) * tick_seconds
    channel.last_tick_at = now

    content_row = await session.execute(select(Content).where(Content.id == channel.content_id))
    content = content_row.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Not found")

    creator_row = await session.execute(select(User).where(User.id == content.creator_id))
    creator = creator_row.scalar_one_or_none()
    if creator is None:
        raise HTTPException(status_code=404, detail="Not found")

    did_settle, tx_id, settled_amount = await _settle_unpaid_amount(
        session=session,
        circle=circle,
        channel=channel,
        content=content,
        viewer=user,
        creator=creator,
        now=now,
        force=False,
    )

    await session.commit()
    await session.refresh(channel)

    base = _channel_response(channel)
    return TickResponse(
        **base.model_dump(),
        tick_seconds=tick_seconds,
        did_settle=did_settle,
        settlement_tx_id=tx_id,
        settlement_amount=settled_amount,
    )


@router.post("/close", response_model=TickResponse)
async def close_channel(
    body: ChannelCloseRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    circle: CircleWalletsClient = Depends(get_circle_wallets_client),
) -> TickResponse:
    now = _utcnow()

    result = await session.execute(
        select(PaymentChannel).where(PaymentChannel.id == body.channel_id, PaymentChannel.user_id == user.id).with_for_update()
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Not found")
    if channel.status != "active":
        raise HTTPException(status_code=400, detail="Channel is not active")

    content_row = await session.execute(select(Content).where(Content.id == channel.content_id))
    content = content_row.scalar_one_or_none()
    if content is None:
        raise HTTPException(status_code=404, detail="Not found")

    creator_row = await session.execute(select(User).where(User.id == content.creator_id))
    creator = creator_row.scalar_one_or_none()
    if creator is None:
        raise HTTPException(status_code=404, detail="Not found")

    did_settle, tx_id, settled_amount = await _settle_unpaid_amount(
        session=session,
        circle=circle,
        channel=channel,
        content=content,
        viewer=user,
        creator=creator,
        now=now,
        force=True,
    )

    channel.status = "closed"
    channel.closed_at = now

    await session.commit()
    await session.refresh(channel)

    base = _channel_response(channel)
    return TickResponse(
        **base.model_dump(),
        tick_seconds=0,
        did_settle=did_settle,
        settlement_tx_id=tx_id,
        settlement_amount=settled_amount,
    )
