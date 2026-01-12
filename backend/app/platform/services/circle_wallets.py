from dataclasses import dataclass
import asyncio

from circle.web3 import developer_controlled_wallets, utils

from app.platform.config import settings


@dataclass(frozen=True)
class CreatedWallet:
    circle_wallet_id: str
    wallet_address: str


class CircleWalletsClient:
    async def create_developer_wallet(self) -> CreatedWallet:
        if not settings.circle_api_key or not settings.circle_wallet_set_id or not settings.circle_entity_secret:
            raise RuntimeError("Circle Wallets not configured")

        client = utils.init_developer_controlled_wallets_client(
            api_key=settings.circle_api_key,
            entity_secret=settings.circle_entity_secret,
        )

        api_instance = developer_controlled_wallets.WalletsApi(client)

        request = developer_controlled_wallets.CreateWalletRequest.from_dict(
            {
                "accountType": "EOA",
                "blockchains": ["ARC-TESTNET"],
                "count": 1,
                "walletSetId": settings.circle_wallet_set_id,
            }
        )

        response = await asyncio.to_thread(api_instance.create_wallet, request)

        data = getattr(response, "data", None)
        wallets = getattr(data, "wallets", None) if data is not None else None
        if not wallets:
            raise RuntimeError("Circle wallet creation returned no wallets")

        wallet = wallets[0]
        actual = getattr(wallet, "actual_instance", wallet)

        wallet_id = getattr(actual, "id", None)
        address = getattr(actual, "address", None)
        if not wallet_id or not address:
            raise RuntimeError("Circle wallet creation returned invalid wallet")

        return CreatedWallet(circle_wallet_id=str(wallet_id), wallet_address=str(address))
