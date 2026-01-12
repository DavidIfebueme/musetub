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
async def test_circle_register_flow_live() -> None:
    if os.environ.get("RUN_CIRCLE_LIVE_TESTS") != "1":
        pytest.skip("Set RUN_CIRCLE_LIVE_TESTS=1 to run Circle live test")

    for required in ["CIRCLE_API_KEY", "CIRCLE_ENTITY_SECRET", "CIRCLE_WALLET_SET_ID"]:
        if not os.environ.get(required):
            pytest.skip(f"{required} not set")

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

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            email = f"circle-{uuid.uuid4()}@example.com"
            register_response = await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": "pass1234", "is_creator": False},
            )
            assert register_response.status_code == 200
            token = register_response.json()["access_token"]

            me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
            assert me.status_code == 200
            payload = me.json()
            assert payload["email"] == email
            assert isinstance(payload.get("wallet_address"), str) and payload["wallet_address"]
            assert isinstance(payload.get("circle_wallet_id"), str) and payload["circle_wallet_id"]
    finally:
        await engine.dispose()
