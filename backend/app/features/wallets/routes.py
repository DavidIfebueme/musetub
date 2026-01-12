from fastapi import APIRouter, Depends

from app.features.wallets.schemas import FundTestnetResponse
from app.platform.security import get_current_user

router = APIRouter(prefix="/wallets")


@router.post("/fund-testnet", response_model=FundTestnetResponse)
async def fund_testnet(user=Depends(get_current_user)) -> FundTestnetResponse:
    instructions = "Fund this wallet on Arc testnet USDC using Circle's testnet funding flow for your account."
    return FundTestnetResponse(
        wallet_address=user.wallet_address or "",
        instructions=instructions,
        docs_url="https://developers.circle.com",
    )
