from dataclasses import dataclass
import asyncio
import json
from uuid import uuid4

from circle.web3 import developer_controlled_wallets, utils

from app.platform.config import settings


@dataclass(frozen=True)
class CreatedWallet:
    circle_wallet_id: str
    wallet_address: str


class CircleWalletsClient:
    def _init_client(self):
        if not settings.circle_api_key or not settings.circle_entity_secret:
            raise RuntimeError("Circle Wallets not configured")

        return utils.init_developer_controlled_wallets_client(
            api_key=settings.circle_api_key,
            entity_secret=settings.circle_entity_secret,
        )

    def _entity_secret_ciphertext(self) -> str:
        if not settings.circle_api_key or not settings.circle_entity_secret:
            raise RuntimeError("Circle Wallets not configured")
        return utils.generate_entity_secret_ciphertext(settings.circle_api_key, settings.circle_entity_secret)

    async def create_developer_wallet(self) -> CreatedWallet:
        if not settings.circle_api_key or not settings.circle_wallet_set_id or not settings.circle_entity_secret:
            raise RuntimeError("Circle Wallets not configured")

        client = self._init_client()

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

    async def sign_typed_data(self, *, wallet_id: str, blockchain: str, typed_data: dict, memo: str | None = None) -> str:
        client = self._init_client()
        api_instance = developer_controlled_wallets.SigningApi(client)

        request = developer_controlled_wallets.SignTypedDataRequest.from_dict(
            {
                "walletId": wallet_id,
                "blockchain": blockchain,
                "data": json.dumps(typed_data, separators=(",", ":"), sort_keys=True),
                "memo": memo or "",
                "entitySecretCiphertext": self._entity_secret_ciphertext(),
            }
        )

        response = await asyncio.to_thread(api_instance.sign_typed_data, request)
        data = getattr(response, "data", None)
        signature = getattr(data, "signature", None) if data is not None else None
        if not signature:
            raise RuntimeError("Circle typed data signing returned no signature")

        return str(signature)

    async def create_contract_execution_transaction(
        self,
        *,
        wallet_id: str,
        blockchain: str,
        contract_address: str,
        abi_function_signature: str,
        abi_parameters: list,
        fee_level: str = "MEDIUM",
        ref_id: str | None = None,
    ) -> str:
        client = self._init_client()
        api_instance = developer_controlled_wallets.TransactionsApi(client)

        request = developer_controlled_wallets.CreateContractExecutionTransactionForDeveloperRequest.from_dict(
            {
                "idempotencyKey": str(uuid4()),
                "blockchain": blockchain,
                "walletId": wallet_id,
                "contractAddress": contract_address,
                "abiFunctionSignature": abi_function_signature,
                "abiParameters": abi_parameters,
                "feeLevel": fee_level,
                "refId": ref_id or "",
                "entitySecretCiphertext": self._entity_secret_ciphertext(),
            }
        )

        response = await asyncio.to_thread(api_instance.create_contract_execution_transaction, request)
        data = getattr(response, "data", None)
        tx_id = getattr(data, "id", None) if data is not None else None
        if not tx_id:
            raise RuntimeError("Circle contract execution returned no transaction id")

        return str(tx_id)
