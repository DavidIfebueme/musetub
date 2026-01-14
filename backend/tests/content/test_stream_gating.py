import os
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.main import create_app


@pytest.mark.asyncio
async def test_stream_requires_active_channel_and_fresh_ticks(monkeypatch: pytest.MonkeyPatch) -> None:
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

        from app.features.payments import routes as payments_routes
        from app.features.content import routes as content_routes

        base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        tick_times = [base + timedelta(seconds=11)]

        def fake_payment_now() -> datetime:
            return tick_times.pop(0) if tick_times else base + timedelta(seconds=999)

        stream_times = [
            base + timedelta(seconds=20),
            base + timedelta(seconds=40),
        ]

        def fake_stream_now() -> datetime:
            return stream_times.pop(0) if stream_times else base + timedelta(seconds=999)

        monkeypatch.setattr(payments_routes, "_utcnow", fake_payment_now)
        monkeypatch.setattr(content_routes, "_utcnow", fake_stream_now)

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

            stream_no_channel = await client.get(
                f"/api/v1/content/{content_id}/stream",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert stream_no_channel.status_code == 402

            open_resp = await client.post(
                "/api/v1/payments/channel/open",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"content_id": content_id},
            )
            assert open_resp.status_code == 200
            channel_id = open_resp.json()["id"]

            stream_no_tick = await client.get(
                f"/api/v1/content/{content_id}/stream",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert stream_no_tick.status_code == 402

            tick = await client.post(
                "/api/v1/payments/channel/tick",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"channel_id": channel_id},
            )
            assert tick.status_code == 200

            stream_fresh = await client.get(
                f"/api/v1/content/{content_id}/stream",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert stream_fresh.status_code == 200
            assert stream_fresh.json()["playback_url"].endswith("/bafytestcid")

            stream_stale = await client.get(
                f"/api/v1/content/{content_id}/stream",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert stream_stale.status_code == 402
    finally:
        await engine.dispose()
