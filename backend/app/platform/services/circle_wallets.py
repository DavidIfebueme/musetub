from dataclasses import dataclass

from app.platform.config import settings


@dataclass(frozen=True)
class CreatedWallet:
    circle_wallet_id: str
    wallet_address: str


class CircleWalletsClient:
    async def create_developer_wallet(self) -> CreatedWallet:
        if not settings.circle_api_key or not settings.circle_wallet_set_id:
            raise RuntimeError("Circle Wallets not configured")

        raise NotImplementedError()
