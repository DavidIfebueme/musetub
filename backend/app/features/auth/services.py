from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import TokenResponse
from app.platform.db.models import User
from app.platform.security import create_access_token, hash_password, verify_password
from app.platform.services.circle_wallets import CircleWalletsClient


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=400, detail=detail)


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid credentials")


async def register_user(
    session: AsyncSession,
    circle: CircleWalletsClient,
    email: str,
    password: str,
    is_creator: bool,
) -> TokenResponse:
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise _bad_request("Email already registered")

    created_wallet = await circle.create_developer_wallet()

    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_creator=is_creator,
        circle_wallet_id=created_wallet.circle_wallet_id,
        wallet_address=created_wallet.wallet_address,
    )

    session.add(user)
    await session.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


async def login_user(session: AsyncSession, email: str, password: str) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise _unauthorized()

    if not verify_password(password, user.hashed_password):
        raise _unauthorized()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
