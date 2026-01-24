import os
import asyncio

import pytest
import httpx

from app.platform.config import settings
from app.platform.services.ipfs import IPFSClient


@pytest.mark.asyncio
async def test_ipfs_add_and_gateway_fetch() -> None:
    provider = (os.environ.get("IPFS_PROVIDER") or "kubo").strip().lower()
    if provider != "kubo":
        pytest.skip("IPFS integration test only runs against local Kubo")

    api_url = os.environ.get("IPFS_API_URL") or settings.ipfs_api_url
    gateway_url = os.environ.get("IPFS_GATEWAY_URL") or settings.ipfs_gateway_url

    client = IPFSClient(api_url=api_url, gateway_url=gateway_url)

    try:
        cid = await client.add_bytes(b"hello", filename="hello.txt")
    except Exception:
        pytest.skip("IPFS API not reachable")

    playback = client.playback_url(cid)

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
        last_error: Exception | None = None
        for _ in range(20):
            try:
                resp = await http.get(playback)
                if resp.status_code == 200:
                    assert resp.content == b"hello"
                    return
                last_error = RuntimeError(f"unexpected status {resp.status_code}")
            except Exception as exc:
                last_error = exc
            await asyncio.sleep(0.25)

    if last_error is not None:
        raise last_error
