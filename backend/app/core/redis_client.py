"""Shared Redis client with fast-fail timeouts for local development."""
import redis.asyncio as redis

from app.core.config import settings
from app.core.logging_config import logger

_client: redis.Redis | None = None
_available: bool | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.25,
            socket_timeout=0.25,
        )
    return _client


async def is_redis_available() -> bool:
    """Ping Redis once per process; skip slow retries when Redis is not running locally."""
    global _available
    if _available is not None:
        return _available
    try:
        await get_redis().ping()
        _available = True
    except Exception as exc:
        _available = False
        logger.info(f"Redis unavailable, using in-memory fallbacks: {exc}")
    return _available
