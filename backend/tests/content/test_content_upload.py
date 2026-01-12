import os
import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.main import create_app


@pytest.mark.asyncio
async def test_creator_can_upload_and_browse(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))

        alembic_cfg = Config("alembic.ini")
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

        app = create_app()

        from app.features.auth.routes import get_circle_client
        from app.platform.services.circle_wallets import CreatedWallet

        class _FakeCircle:
            async def create_developer_wallet(self) -> CreatedWallet:
                return CreatedWallet(circle_wallet_id="cw_test", wallet_address="0xabc")

        from app.features.content.routes import get_ipfs_client

        class _FakeIPFS:
            async def add_bytes(self, data: bytes, filename: str) -> str:
                return "bafytestcid"

            def playback_url(self, cid: str) -> str:
                return f"http://localhost:8080/ipfs/{cid}"

        app.dependency_overrides[get_circle_client] = lambda: _FakeCircle()
        app.dependency_overrides[get_ipfs_client] = lambda: _FakeIPFS()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            email = f"creator-{uuid.uuid4()}@example.com"
            register_response = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "pass1234", "is_creator": True},
            )
            assert register_response.status_code == 200
            token = register_response.json()["access_token"]

            upload = await client.post(
                "/api/v1/content/upload",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "title": "Test",
                    "description": "Desc",
                    "content_type": "tutorial",
                    "duration_seconds": "120",
                    "resolution": "1080p",
                    "bitrate_tier": "high",
                    "engagement_intent": "learn",
                },
                files={"file": ("hello.txt", b"hello", "text/plain")},
            )
            assert upload.status_code == 200
            payload = upload.json()
            assert payload["ipfs_cid"] == "bafytestcid"
            assert payload["playback_url"].endswith("/bafytestcid")
            assert 1 <= payload["quality_score"] <= 10
            assert payload["suggested_price_per_second"] > 0
            assert payload["price_per_second"] > 0
            assert isinstance(payload["pricing_explanation"], str) and payload["pricing_explanation"]

            lst = await client.get("/api/v1/content")
            assert lst.status_code == 200
            items = lst.json()
            assert len(items) >= 1
            assert items[0]["id"] == payload["id"]

            detail = await client.get(f"/api/v1/content/{payload['id']}")
            assert detail.status_code == 200
            assert detail.json()["id"] == payload["id"]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_non_creator_cannot_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))

        alembic_cfg = Config("alembic.ini")
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

        app = create_app()

        from app.features.auth.routes import get_circle_client
        from app.platform.services.circle_wallets import CreatedWallet

        class _FakeCircle:
            async def create_developer_wallet(self) -> CreatedWallet:
                return CreatedWallet(circle_wallet_id="cw_test", wallet_address="0xabc")

        from app.features.content.routes import get_ipfs_client

        class _FakeIPFS:
            async def add_bytes(self, data: bytes, filename: str) -> str:
                return "bafytestcid"

            def playback_url(self, cid: str) -> str:
                return f"http://localhost:8080/ipfs/{cid}"

        app.dependency_overrides[get_circle_client] = lambda: _FakeCircle()
        app.dependency_overrides[get_ipfs_client] = lambda: _FakeIPFS()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            email = f"user-{uuid.uuid4()}@example.com"
            register_response = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "pass1234", "is_creator": False},
            )
            assert register_response.status_code == 200
            token = register_response.json()["access_token"]

            upload = await client.post(
                "/api/v1/content/upload",
                headers={"Authorization": f"Bearer {token}"},
                data={
                    "title": "Test",
                    "description": "Desc",
                    "content_type": "tutorial",
                    "duration_seconds": "120",
                    "resolution": "1080p",
                    "bitrate_tier": "high",
                    "engagement_intent": "learn",
                },
                files={"file": ("hello.txt", b"hello", "text/plain")},
            )
            assert upload.status_code == 403
    finally:
        await engine.dispose()
