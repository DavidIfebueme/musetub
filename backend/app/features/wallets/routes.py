from __future__ import annotations

from Crypto.Hash import keccak
from fastapi import APIRouter, Depends
import httpx

from app.features.wallets.schemas import ArcBlockHeightResponse
from app.features.wallets.schemas import FundTestnetResponse
from app.features.wallets.schemas import UsdcBalanceResponse
from app.platform.config import settings
from app.platform.security import get_current_user
from app.platform.services.chain import usdc_minor_units_to_decimal

router = APIRouter(prefix="/wallets")


async def _arc_rpc(method: str, params: list) -> dict:
    if not settings.arc_rpc_url:
        raise RuntimeError("ARC RPC not configured")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(settings.arc_rpc_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"ARC RPC error: {data['error']}")

    if not isinstance(data, dict) or "result" not in data:
        raise RuntimeError("ARC RPC returned no result")

    return data


def _erc20_balance_of_calldata(address: str) -> str:
    if not isinstance(address, str) or not address.startswith("0x") or len(address) != 42:
        raise ValueError("Invalid address")

    k = keccak.new(digest_bits=256)
    k.update(b"balanceOf(address)")
    selector = k.digest()[:4].hex()

    addr_hex = address[2:].lower()
    padded = ("0" * 24) + addr_hex
    return "0x" + selector + padded


@router.post("/fund-testnet", response_model=FundTestnetResponse)
async def fund_testnet(user=Depends(get_current_user)) -> FundTestnetResponse:
    instructions = "Fund this wallet on Arc testnet USDC using Circle's testnet funding flow for your account."
    return FundTestnetResponse(
        wallet_address=user.wallet_address or "",
        instructions=instructions,
        docs_url="https://developers.circle.com",
    )


@router.get("/arc-block-height", response_model=ArcBlockHeightResponse)
async def arc_block_height() -> ArcBlockHeightResponse:
    data = await _arc_rpc("eth_blockNumber", [])
    result = data.get("result")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise RuntimeError("ARC RPC returned invalid blockNumber")

    return ArcBlockHeightResponse(block_height=int(result, 16))


@router.get("/usdc-balance", response_model=UsdcBalanceResponse)
async def usdc_balance(user=Depends(get_current_user)) -> UsdcBalanceResponse:
    if not user.wallet_address:
        raise RuntimeError("User has no wallet address")
    if not settings.usdc_address:
        raise RuntimeError("USDC address not configured")

    call = {
        "to": settings.usdc_address,
        "data": _erc20_balance_of_calldata(user.wallet_address),
    }

    data = await _arc_rpc("eth_call", [call, "latest"])
    result = data.get("result")
    if not isinstance(result, str) or not result.startswith("0x"):
        raise RuntimeError("ARC RPC returned invalid eth_call result")

    balance_minor = int(result, 16)
    balance = str(usdc_minor_units_to_decimal(balance_minor))

    return UsdcBalanceResponse(
        wallet_address=user.wallet_address,
        usdc_address=settings.usdc_address,
        balance_minor=balance_minor,
        balance=balance,
    )
