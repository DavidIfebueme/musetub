from sqlalchemy.ext.asyncio import AsyncEngine

from app.platform.db.base import Base


async def create_all(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
