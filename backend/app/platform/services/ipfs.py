import json

import httpx

from app.platform.config import settings


class IPFSClient:
    def __init__(self, api_url: str | None = None, gateway_url: str | None = None) -> None:
        self._api_url = (api_url or settings.ipfs_api_url).rstrip("/")
        self._gateway_url = (gateway_url or settings.ipfs_gateway_url).rstrip("/")

    async def add_bytes(self, data: bytes, filename: str) -> str:
        url = f"{self._api_url}/api/v0/add"
        files = {"file": (filename, data, "application/octet-stream")}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, files=files)
            response.raise_for_status()

        cid = self._parse_add_response_for_cid(response.text)
        if not cid:
            raise RuntimeError("IPFS add did not return a CID")
        return cid

    def playback_url(self, cid: str) -> str:
        return f"{self._gateway_url}/{cid}"

    @staticmethod
    def _parse_add_response_for_cid(body: str) -> str:
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        if not lines:
            return ""

        for line in reversed(lines):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            cid = payload.get("Hash")
            if isinstance(cid, str) and cid:
                return cid

        return ""
