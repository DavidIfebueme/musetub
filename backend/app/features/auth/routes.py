from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.features.auth.services import login_user, register_user
from app.platform.db.session import get_session
from app.platform.security import get_current_user
from app.platform.services.circle_wallets import CircleWalletsClient

router = APIRouter(prefix="/auth")


def get_circle_client() -> CircleWalletsClient:
    return CircleWalletsClient()


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    circle: CircleWalletsClient = Depends(get_circle_client),
) -> TokenResponse:
    return await register_user(
        session=session,
        circle=circle,
        email=str(body.email),
        password=body.password,
        is_creator=body.is_creator,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    return await login_user(session=session, email=str(body.email), password=body.password)


@router.get("/me", response_model=MeResponse)
async def me(user=Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        is_creator=user.is_creator,
        wallet_address=user.wallet_address,
        circle_wallet_id=user.circle_wallet_id,
    )
