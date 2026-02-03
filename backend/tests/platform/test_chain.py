from decimal import Decimal

import pytest

from app.platform.services.chain import (
    ChainClient,
    ChainConfig,
    usdc_decimal_to_minor_units,
    usdc_minor_units_to_decimal,
)


def test_usdc_unit_conversions_round_trip() -> None:
    amount = Decimal("12.345678")
    minor = usdc_decimal_to_minor_units(amount)
    assert minor == 12_345_678

    back = usdc_minor_units_to_decimal(minor)
    assert back == amount


def test_usdc_decimal_to_minor_units_rounds_down() -> None:
    amount = Decimal("1.9999999")
    minor = usdc_decimal_to_minor_units(amount)
    assert minor == 1_999_999


def test_usdc_decimal_to_minor_units_rejects_negative() -> None:
    with pytest.raises(ValueError):
        usdc_decimal_to_minor_units(Decimal("-0.1"))


def test_erc3009_typed_data_shape() -> None:
    client = ChainClient(
        ChainConfig(
            rpc_url="http://localhost:8545",
            chain_id=123,
            usdc_address="0x0000000000000000000000000000000000000001",
            escrow_address="0x0000000000000000000000000000000000000002",
            usdc_name="USDC",
            usdc_version="2",
        )
    )

    typed = client.erc3009_receive_with_authorization_typed_data(
        from_address="0x0000000000000000000000000000000000000011",
        to_address="0x0000000000000000000000000000000000000022",
        value=123,
        valid_after=1,
        valid_before=2,
        nonce="0x" + "11" * 32,
    )

    assert typed["primaryType"] == "ReceiveWithAuthorization"
    assert typed["domain"]["chainId"] == 123
    assert typed["domain"]["verifyingContract"] == "0x0000000000000000000000000000000000000001"
    assert typed["message"]["value"] == 123
