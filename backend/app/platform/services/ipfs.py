import json

import httpx

from app.platform.config import settings


class IPFSClient:
    def __init__(self, api_url: str | None = None, gateway_url: str | None = None) -> None:
        self._provider = (settings.ipfs_provider or "kubo").strip().lower()
        self._api_url = (api_url or settings.ipfs_api_url).rstrip("/")
        self._gateway_url = (gateway_url or settings.ipfs_gateway_url).rstrip("/")
        self._pinata_api_url = (settings.pinata_api_url or "https://api.pinata.cloud").rstrip("/")
        self._pinata_jwt = settings.pinata_jwt

    async def add_bytes(self, data: bytes, filename: str) -> str:
        if self._provider == "pinata":
            return await self._pinata_add_bytes(data=data, filename=filename)

        url = f"{self._api_url}/api/v0/add"
        files = {"file": (filename, data, "application/octet-stream")}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, files=files)
            response.raise_for_status()

        cid = self._parse_add_response_for_cid(response.text)
        if not cid:
            raise RuntimeError("IPFS add did not return a CID")
        return cid

    async def _pinata_add_bytes(self, data: bytes, filename: str) -> str:
        if not self._pinata_jwt:
            raise RuntimeError("PINATA_JWT is required when IPFS_PROVIDER=pinata")

        url = f"{self._pinata_api_url}/pinning/pinFileToIPFS"
        headers = {"Authorization": f"Bearer {self._pinata_jwt}"}
        files = {"file": (filename, data, "application/octet-stream")}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, files=files)
            response.raise_for_status()
            payload = response.json()

        cid = payload.get("IpfsHash")
        if isinstance(cid, str) and cid:
            return cid

        raise RuntimeError("Pinata upload did not return IpfsHash")

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
