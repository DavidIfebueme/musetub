import types

import pytest

from app.platform.config import settings
from app.platform.services.circle_wallets import CircleWalletsClient


@pytest.mark.asyncio
async def test_sign_typed_data_uses_entity_secret_ciphertext(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "circle_api_key", "key")
    monkeypatch.setattr(settings, "circle_entity_secret", "secret")

    calls = {}

    def fake_init(*, api_key: str, entity_secret: str):
        calls["init"] = (api_key, entity_secret)
        return object()

    def fake_cipher(api_key: str, entity_secret: str) -> str:
        calls["cipher"] = (api_key, entity_secret)
        return "ciphertext"

    class FakeSigningApi:
        def __init__(self, client):
            self.client = client

        def sign_typed_data(self, request):
            calls["request"] = request
            return types.SimpleNamespace(data=types.SimpleNamespace(signature="0xsig"))

    monkeypatch.setattr("app.platform.services.circle_wallets.utils.init_developer_controlled_wallets_client", fake_init)
    monkeypatch.setattr("app.platform.services.circle_wallets.utils.generate_entity_secret_ciphertext", fake_cipher)
    monkeypatch.setattr("app.platform.services.circle_wallets.developer_controlled_wallets.SigningApi", FakeSigningApi)

    client = CircleWalletsClient()
    sig = await client.sign_typed_data(wallet_id="wid", blockchain="ARC-TESTNET", typed_data={"x": 1})

    assert sig == "0xsig"
    assert calls["init"] == ("key", "secret")
    assert calls["cipher"] == ("key", "secret")


@pytest.mark.asyncio
async def test_create_contract_execution_transaction_requires_tx_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "circle_api_key", "key")
    monkeypatch.setattr(settings, "circle_entity_secret", "secret")

    def fake_init(*, api_key: str, entity_secret: str):
        return object()

    def fake_cipher(api_key: str, entity_secret: str) -> str:
        return "ciphertext"

    class FakeTransactionsApi:
        def __init__(self, client):
            self.client = client

        def create_contract_execution_transaction(self, request):
            return types.SimpleNamespace(data=types.SimpleNamespace(id=None))

    monkeypatch.setattr("app.platform.services.circle_wallets.utils.init_developer_controlled_wallets_client", fake_init)
    monkeypatch.setattr("app.platform.services.circle_wallets.utils.generate_entity_secret_ciphertext", fake_cipher)
    monkeypatch.setattr("app.platform.services.circle_wallets.developer_controlled_wallets.TransactionsApi", FakeTransactionsApi)

    client = CircleWalletsClient()
    with pytest.raises(RuntimeError):
        await client.create_contract_execution_transaction(
            wallet_id="wid",
            blockchain="ARC-TESTNET",
            contract_address="0x1",
            abi_function_signature="f()",
            abi_parameters=[],
        )

