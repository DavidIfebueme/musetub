from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from app.platform.config import settings


USDC_DECIMALS = 6


@dataclass(frozen=True)
class ChainConfig:
    rpc_url: str
    chain_id: int
    usdc_address: str
    escrow_address: str
    usdc_name: str
    usdc_version: str


class ChainClient:
    def __init__(self, config: ChainConfig) -> None:
        self._config = config

    @classmethod
    def from_settings(cls) -> "ChainClient":
        if not settings.arc_rpc_url:
            raise RuntimeError("ARC RPC not configured")
        if settings.arc_chain_id is None:
            raise RuntimeError("ARC chain id not configured")
        if not settings.usdc_address:
            raise RuntimeError("USDC address not configured")
        if not settings.escrow_address:
            raise RuntimeError("Escrow address not configured")

        return cls(
            ChainConfig(
                rpc_url=settings.arc_rpc_url,
                chain_id=settings.arc_chain_id,
                usdc_address=settings.usdc_address,
                escrow_address=settings.escrow_address,
                usdc_name=settings.usdc_name,
                usdc_version=settings.usdc_version,
            )
        )

    @property
    def config(self) -> ChainConfig:
        return self._config

    def erc3009_receive_with_authorization_typed_data(
        self,
        *,
        from_address: str,
        to_address: str,
        value: int,
        valid_after: int,
        valid_before: int,
        nonce: str,
    ) -> dict:
        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "ReceiveWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ],
            },
            "primaryType": "ReceiveWithAuthorization",
            "domain": {
                "name": self._config.usdc_name,
                "version": self._config.usdc_version,
                "chainId": self._config.chain_id,
                "verifyingContract": self._config.usdc_address,
            },
            "message": {
                "from": from_address,
                "to": to_address,
                "value": value,
                "validAfter": valid_after,
                "validBefore": valid_before,
                "nonce": nonce,
            },
        }


def usdc_decimal_to_minor_units(amount: Decimal) -> int:
    if amount.is_nan():
        raise ValueError("amount is NaN")
    if amount < 0:
        raise ValueError("amount must be non-negative")

    scale = Decimal(10) ** USDC_DECIMALS
    minor = (amount * scale).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return int(minor)


def usdc_minor_units_to_decimal(amount: int) -> Decimal:
    if amount < 0:
        raise ValueError("amount must be non-negative")

    scale = Decimal(10) ** USDC_DECIMALS
    return Decimal(amount) / scale
