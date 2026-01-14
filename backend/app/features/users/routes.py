from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import MeResponse
from app.features.users.schemas import UserHistoryItem, UserSpendingResponse
from app.platform.db.models import Content, PaymentChannel
from app.platform.db.session import get_session
from app.platform.security import get_current_user

router = APIRouter(prefix="/users")


@router.get("/me", response_model=MeResponse)
async def me(user=Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        is_creator=user.is_creator,
        wallet_address=user.wallet_address,
        circle_wallet_id=user.circle_wallet_id,
    )


@router.get("/me/history", response_model=list[UserHistoryItem])
async def my_history(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[UserHistoryItem]:
    result = await session.execute(
        select(
            PaymentChannel,
            Content.title,
            Content.creator_id,
        )
        .join(Content, Content.id == PaymentChannel.content_id)
        .where(PaymentChannel.user_id == user.id)
        .order_by(PaymentChannel.opened_at.desc())
        .limit(100)
    )

    items: list[UserHistoryItem] = []
    for channel, title, creator_id in result.all():
        items.append(
            UserHistoryItem(
                channel_id=channel.id,
                content_id=channel.content_id,
                content_title=str(title),
                creator_id=str(creator_id),
                status=channel.status,
                price_per_second_locked=int(channel.price_per_second_locked),
                total_seconds_streamed=int(channel.total_seconds_streamed),
                total_amount_owed=int(channel.total_amount_owed),
                total_amount_settled=int(channel.total_amount_settled),
                last_tick_at=channel.last_tick_at,
                last_settlement_at=channel.last_settlement_at,
                opened_at=channel.opened_at,
                closed_at=channel.closed_at,
            )
        )

    return items


@router.get("/me/spending", response_model=UserSpendingResponse)
async def my_spending(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserSpendingResponse:
    result = await session.execute(
        select(
            func.coalesce(func.sum(PaymentChannel.total_seconds_streamed), 0),
            func.coalesce(func.sum(PaymentChannel.total_amount_owed), 0),
            func.coalesce(func.sum(PaymentChannel.total_amount_settled), 0),
        ).where(PaymentChannel.user_id == user.id)
    )

    seconds, owed, settled = result.one()
    return UserSpendingResponse(
        total_seconds_streamed=int(seconds or 0),
        total_amount_owed=int(owed or 0),
        total_amount_settled=int(settled or 0),
    )
