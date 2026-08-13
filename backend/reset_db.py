import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.database.base import Base


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///./app.db", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


asyncio.run(main())
