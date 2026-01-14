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
async def test_open_tick_close_flow(monkeypatch: pytest.MonkeyPatch) -> None:
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

        base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        times = [
            base,
            base + timedelta(seconds=11),
            base + timedelta(seconds=22),
            base + timedelta(seconds=33),
        ]

        def fake_now() -> datetime:
            return times.pop(0) if times else base + timedelta(seconds=999)

        monkeypatch.setattr(payments_routes, "_utcnow", fake_now)

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
            price_per_second = upload.json()["price_per_second"]

            user_email = f"user-{uuid.uuid4()}@example.com"
            user_register = await client.post(
                "/api/v1/auth/register",
                json={"email": user_email, "password": "pass1234", "is_creator": False},
            )
            assert user_register.status_code == 200
            user_token = user_register.json()["access_token"]

            open_resp = await client.post(
                "/api/v1/payments/channel/open",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"content_id": content_id},
            )
            assert open_resp.status_code == 200
            channel_id = open_resp.json()["id"]
            assert open_resp.json()["price_per_second_locked"] == price_per_second

            tick1 = await client.post(
                "/api/v1/payments/channel/tick",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"channel_id": channel_id},
            )
            assert tick1.status_code == 200
            assert tick1.json()["tick_seconds"] == 10
            assert tick1.json()["total_amount_owed"] == price_per_second * 10
            assert tick1.json()["did_settle"] is False

            tick2 = await client.post(
                "/api/v1/payments/channel/tick",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"channel_id": channel_id},
            )
            assert tick2.status_code == 200
            assert tick2.json()["total_amount_owed"] == price_per_second * 20

            tick3 = await client.post(
                "/api/v1/payments/channel/tick",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"channel_id": channel_id},
            )
            assert tick3.status_code == 200
            assert tick3.json()["total_amount_owed"] == price_per_second * 30

            close = await client.post(
                "/api/v1/payments/channel/close",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"channel_id": channel_id},
            )
            assert close.status_code == 200
            assert close.json()["status"] == "closed"
            assert close.json()["did_settle"] is True
            assert close.json()["settlement_amount"] == price_per_second * 30
            assert isinstance(close.json()["settlement_tx_id"], str) and close.json()["settlement_tx_id"]
            assert close.json()["total_amount_settled"] == price_per_second * 30
    finally:
        await engine.dispose()
