"""Create database tables and local storage directories on startup."""
from pathlib import Path

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine
from app.models import *  # noqa: F401,F403 -- register all models on Base.metadata


async def init_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def ensure_directories() -> None:
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
