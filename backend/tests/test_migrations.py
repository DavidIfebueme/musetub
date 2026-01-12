import os
import asyncio

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_migrations_apply_cleanly() -> None:
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

        expected_tables = {
            "alembic_version",
            "users",
            "creator_policies",
            "content",
            "payment_channels",
            "settlements",
            "ai_cache",
        }

        async with engine.connect() as connection:
            def _get_tables(sync_connection):
                from sqlalchemy import inspect

                return set(inspect(sync_connection).get_table_names())

            tables = await connection.run_sync(_get_tables)

        assert expected_tables.issubset(tables)
    finally:
        await engine.dispose()
