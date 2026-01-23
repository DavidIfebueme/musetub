import os
import asyncio
import uuid

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.main import create_app


@pytest.mark.asyncio
async def test_stream_pay_grants_credit(monkeypatch: pytest.MonkeyPatch) -> None:
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
            creator_email = f"creator-{uuid.uuid4()}@example.com"
            creator_register = await client.post(
                "/api/v1/auth/register",
                json={"email": creator_email, "password": "pass1234", "is_creator": True},
            )
            assert creator_register.status_code == 200
            creator_token = creator_register.json()["access_token"]

            upload = await client.post(
                "/api/v1/content/upload",
                headers={"Authorization": f"Bearer {creator_token}"},
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
            content_id = upload.json()["id"]

            user_email = f"user-{uuid.uuid4()}@example.com"
            user_register = await client.post(
                "/api/v1/auth/register",
                json={"email": user_email, "password": "pass1234", "is_creator": False},
            )
            assert user_register.status_code == 200
            user_token = user_register.json()["access_token"]

            pay = await client.post(
                f"/api/v1/content/{content_id}/pay",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert pay.status_code == 200
            assert pay.json()["playback_url"].endswith("/bafytestcid")
            assert "Payment-Response" in pay.headers

            stream = await client.get(
                f"/api/v1/content/{content_id}/stream",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert stream.status_code == 200
            assert stream.json()["playback_url"].endswith("/bafytestcid")
    finally:
        await engine.dispose()
