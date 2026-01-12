from fastapi import APIRouter, Depends

from app.features.auth.schemas import MeResponse
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
