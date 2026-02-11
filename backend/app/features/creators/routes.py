from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Crypto.Hash import keccak

from app.features.creators.schemas import (
    CreatorContentEarningsItem,
    CreatorDashboardResponse,
    CreatorSettlementItem,
    WithdrawResponse,
)
from app.platform.config import settings
from app.platform.db.models import Content, PaymentChannel, Settlement
from app.platform.db.session import get_session
from app.platform.security import get_current_user
from app.platform.services.circle_wallets import CircleWalletsClient
from app.platform.services.chain import ChainClient

try:
    from circle.web3.developer_controlled_wallets.exceptions import BadRequestException
except Exception:  # pragma: no cover
    BadRequestException = None  # type: ignore[assignment]


router = APIRouter(prefix="/creators")


_CREATOR_SHARE_BPS = 9000
_BPS_DENOMINATOR = 10_000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail="Forbidden")


def _creator_share(amount_gross: int) -> int:
    return (int(amount_gross) * _CREATOR_SHARE_BPS) // _BPS_DENOMINATOR


def get_circle_wallets_client() -> CircleWalletsClient:
    return CircleWalletsClient()


def _live_withdraw_enabled() -> bool:
    return bool(
        settings.circle_api_key
        and settings.circle_entity_secret
        and settings.arc_rpc_url
        and settings.arc_chain_id is not None
        and settings.usdc_address
        and settings.escrow_address
    )


def _abi_function_selector(signature: str) -> str:
    h = keccak.new(digest_bits=256)
    h.update(signature.encode("utf-8"))
    return h.hexdigest()[:8]


def _abi_encode_address(address: str) -> str:
    if not address or not isinstance(address, str):
        raise ValueError("Invalid address")
    if not address.startswith("0x") or len(address) != 42:
        raise ValueError("Invalid address")
    return address[2:].lower().rjust(64, "0")


async def _arc_eth_call(to_address: str, data: str) -> str:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": to_address, "data": data}, "latest"],
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(settings.arc_rpc_url, json=payload)
        resp.raise_for_status()
        body = resp.json()
    if "error" in body:
        raise HTTPException(status_code=502, detail=f"Arc RPC error: {body['error']}")
    return str(body.get("result") or "0x0")


async def _get_escrow_creator_balance_minor(creator_wallet_address: str) -> int:
    selector = _abi_function_selector("creatorBalances(address)")
    calldata = "0x" + selector + _abi_encode_address(creator_wallet_address)
    result = await _arc_eth_call(settings.escrow_address, calldata)
    try:
        return int(result, 16)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Arc RPC returned invalid value: {result}") from exc


@router.get("/dashboard", response_model=CreatorDashboardResponse)
async def creator_dashboard(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CreatorDashboardResponse:
    if not getattr(user, "is_creator", False):
        raise _forbidden()

    content_count_row = await session.execute(
        select(func.count()).select_from(Content).where(Content.creator_id == user.id)
    )
    content_count = int(content_count_row.scalar() or 0)

    withdrawable_balance: int | None = None
    if _live_withdraw_enabled() and getattr(user, "wallet_address", None):
        try:
            withdrawable_balance = await _get_escrow_creator_balance_minor(user.wallet_address)
        except Exception:
            pass

    result = await session.execute(
        select(Settlement)
        .join(PaymentChannel, PaymentChannel.id == Settlement.channel_id)
        .join(Content, Content.id == PaymentChannel.content_id)
        .where(Content.creator_id == user.id)
        .order_by(desc(Settlement.created_at))
        .limit(50)
    )
    settlements = list(result.scalars().all())

    content_rows = await session.execute(
        select(Content.id, Content.title, func.coalesce(func.sum(Settlement.amount), 0))
        .select_from(Content)
        .join(PaymentChannel, PaymentChannel.content_id == Content.id)
        .join(Settlement, Settlement.channel_id == PaymentChannel.id)
        .where(Content.creator_id == user.id)
        .group_by(Content.id, Content.title)
        .order_by(desc(func.coalesce(func.sum(Settlement.amount), 0)))
    )
    earnings_by_content: list[CreatorContentEarningsItem] = []
    for content_id, title, gross_sum in content_rows.all():
        gross_int = int(gross_sum or 0)
        earnings_by_content.append(
            CreatorContentEarningsItem(
                content_id=str(content_id),
                title=str(title),
                amount_gross=gross_int,
                amount_creator=_creator_share(gross_int),
            )
        )

    total_gross = sum(item.amount_gross for item in earnings_by_content)
    total_creator = sum(item.amount_creator for item in earnings_by_content)

    recent_items: list[CreatorSettlementItem] = []
    if settlements:
        channel_ids = [s.channel_id for s in settlements]
        channel_rows = await session.execute(
            select(PaymentChannel.id, PaymentChannel.content_id)
            .where(PaymentChannel.id.in_(channel_ids))
        )
        channel_to_content = {str(cid): str(content_id) for cid, content_id in channel_rows.all()}

        for s in settlements:
            gross = int(s.amount)
            recent_items.append(
                CreatorSettlementItem(
                    id=s.id,
                    content_id=channel_to_content.get(s.channel_id, ""),
                    channel_id=s.channel_id,
                    amount_gross=gross,
                    amount_creator=_creator_share(gross),
                    tx_hash=s.tx_hash,
                    created_at=s.created_at,
                )
            )

    return CreatorDashboardResponse(
        total_amount_gross=total_gross,
        total_amount_creator=total_creator,
        withdrawable_balance=withdrawable_balance,
        content_count=content_count,
        platform_fee_bps=_BPS_DENOMINATOR - _CREATOR_SHARE_BPS,
        earnings_by_content=earnings_by_content,
        recent_settlements=recent_items,
    )


@router.get("/content", response_model=list[CreatorContentEarningsItem])
async def creator_content_earnings(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CreatorContentEarningsItem]:
    if not getattr(user, "is_creator", False):
        raise _forbidden()

    rows = await session.execute(
        select(Content.id, Content.title, func.coalesce(func.sum(Settlement.amount), 0))
        .select_from(Content)
        .join(PaymentChannel, PaymentChannel.content_id == Content.id)
        .join(Settlement, Settlement.channel_id == PaymentChannel.id)
        .where(Content.creator_id == user.id)
        .group_by(Content.id, Content.title)
        .order_by(desc(func.coalesce(func.sum(Settlement.amount), 0)))
    )

    items: list[CreatorContentEarningsItem] = []
    for content_id, title, gross_sum in rows.all():
        gross_int = int(gross_sum or 0)
        items.append(
            CreatorContentEarningsItem(
                content_id=str(content_id),
                title=str(title),
                amount_gross=gross_int,
                amount_creator=_creator_share(gross_int),
            )
        )

    return items


@router.get("/settlements", response_model=list[CreatorSettlementItem])
async def creator_settlements(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CreatorSettlementItem]:
    if not getattr(user, "is_creator", False):
        raise _forbidden()

    result = await session.execute(
        select(Settlement)
        .join(PaymentChannel, PaymentChannel.id == Settlement.channel_id)
        .join(Content, Content.id == PaymentChannel.content_id)
        .where(Content.creator_id == user.id)
        .order_by(desc(Settlement.created_at))
        .limit(200)
    )
    settlements = list(result.scalars().all())
    if not settlements:
        return []

    channel_ids = [s.channel_id for s in settlements]
    channel_rows = await session.execute(
        select(PaymentChannel.id, PaymentChannel.content_id).where(PaymentChannel.id.in_(channel_ids))
    )
    channel_to_content = {str(cid): str(content_id) for cid, content_id in channel_rows.all()}

    items: list[CreatorSettlementItem] = []
    for s in settlements:
        gross = int(s.amount)
        items.append(
            CreatorSettlementItem(
                id=s.id,
                content_id=channel_to_content.get(s.channel_id, ""),
                channel_id=s.channel_id,
                amount_gross=gross,
                amount_creator=_creator_share(gross),
                tx_hash=s.tx_hash,
                created_at=s.created_at,
            )
        )

    return items


@router.post("/withdraw", response_model=WithdrawResponse)
async def withdraw_creator(
    user=Depends(get_current_user),
    circle: CircleWalletsClient = Depends(get_circle_wallets_client),
) -> WithdrawResponse:
    if not getattr(user, "is_creator", False):
        raise _forbidden()

    if _live_withdraw_enabled():
        if not user.circle_wallet_id:
            raise HTTPException(status_code=400, detail="Creator wallet not available")

        creator_balance = None
        if getattr(user, "wallet_address", None):
            creator_balance = await _get_escrow_creator_balance_minor(user.wallet_address)
            if creator_balance <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Nothing to withdraw yet (on-chain creator balance is 0). "
                        "This value increases only after on-chain payments have executed successfully against the escrow contract. "
                        "Common causes: (1) you are running in simulated mode (payments are recorded in Postgres but no on-chain USDC moves), "
                        "or (2) the most recent Circle contract execution transaction is still pending/failed. "
                        "Check the payment/withdraw tx status via GET /wallets/transactions/{tx_id} and ensure the payer wallet is funded with USDC."
                    ),
                )

        chain = ChainClient.from_settings()
        try:
            tx_id = await circle.create_contract_execution_transaction(
                wallet_id=user.circle_wallet_id,
                blockchain=settings.circle_blockchain,
                contract_address=chain.config.escrow_address,
                abi_function_signature="withdrawCreator()",
                abi_parameters=[],
                ref_id=f"creator-withdraw:{user.id}",
            )
            return WithdrawResponse(tx_id=tx_id)
        except Exception as exc:
            message = str(exc)
            lowered = message.lower()

            if "native tokens" in lowered or "insufficient" in lowered:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Withdraw failed: the creator Circle wallet likely has insufficient Arc testnet native token "
                        "to pay transaction fees (gas). Fund the creator wallet with a small amount of the chain's native token, "
                        "then retry."
                    ),
                ) from exc

            if BadRequestException is not None and isinstance(exc, BadRequestException):
                raise HTTPException(status_code=400, detail=f"Circle withdraw failed: {message}") from exc

            raise HTTPException(status_code=502, detail=f"Circle withdraw failed: {message}") from exc

    return WithdrawResponse(tx_id=f"simulated:{uuid4()}")
