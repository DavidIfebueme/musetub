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
from app.platform.db.base import Base
import app.platform.db.models


@pytest.mark.asyncio
async def test_register_login_me_flow(monkeypatch: pytest.MonkeyPatch) -> None:
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

        app.dependency_overrides[get_circle_client] = lambda: _FakeCircle()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            email = f"user-{uuid.uuid4()}@example.com"
            register_response = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "pass1234", "is_creator": False},
            )
            assert register_response.status_code == 200
            token = register_response.json()["access_token"]

            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "pass1234"},
            )
            assert login_response.status_code == 200

            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert me_response.status_code == 200
            payload = me_response.json()
            assert payload["email"] == email
            assert payload["circle_wallet_id"] == "cw_test"
            assert payload["wallet_address"] == "0xabc"
    finally:
        await engine.dispose()
