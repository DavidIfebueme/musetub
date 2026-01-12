import os
import asyncio

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


@pytest.mark.asyncio
async def test_database_url_connects() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        last_error: Exception | None = None
        for _ in range(30):
            try:
                async with engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.5)

        if last_error is not None:
            raise last_error
    finally:
        await engine.dispose()
