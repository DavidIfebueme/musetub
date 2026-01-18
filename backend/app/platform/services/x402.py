import base64
import json
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class X402Settlement:
    transaction: str
    payer: str


def decode_payment_signature(header_value: str) -> dict:
    raw = base64.b64decode(header_value.encode("utf-8"))
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("invalid payment payload")
    return obj


def encode_payment_response(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def build_402_body(*, url: str, description: str, mime_type: str, accepts: list[dict]) -> dict:
    return {
        "x402Version": 2,
        "error": "Payment required",
        "resource": {
            "url": url,
            "description": description,
            "mimeType": mime_type,
        },
        "accepts": accepts,
    }


def build_exact_accept(*, network: str, asset: str, amount: int, pay_to: str, max_timeout_seconds: int, extra: dict) -> dict:
    return {
        "scheme": "exact",
        "network": network,
        "asset": asset,
        "amount": str(amount),
        "payTo": pay_to,
        "maxTimeoutSeconds": max_timeout_seconds,
        "extra": extra,
    }


async def verify_and_settle_via_sidecar(*, sidecar_url: str, payment_payload: dict, requirements: dict) -> X402Settlement:
    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{sidecar_url.rstrip('/')}/verify-settle",
            json={"paymentPayload": payment_payload, "requirements": requirements},
        )
        resp.raise_for_status()
        data = resp.json()

    transaction = data.get("transaction")
    payer = data.get("payer")
    if not isinstance(transaction, str) or not transaction:
        raise ValueError("missing transaction")
    if not isinstance(payer, str) or not payer:
        payer = "unknown"
    return X402Settlement(transaction=transaction, payer=payer)


async def verify_and_settle_simulated(*, payment_payload: dict) -> X402Settlement:
    payer = "unknown"
    if isinstance(payment_payload.get("payer"), str):
        payer = payment_payload["payer"]

    transaction = "simulated_x402_tx"
    if isinstance(payment_payload.get("transaction"), str):
        transaction = payment_payload["transaction"]

    return X402Settlement(transaction=transaction, payer=payer)
