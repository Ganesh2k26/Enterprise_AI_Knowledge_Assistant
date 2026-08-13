"""
Refresh-token rotation support: every refresh token is single-use. When a
refresh token is redeemed we blacklist its jti in an in-memory set for local
runs and fall back to Redis when it is available.
"""
from app.core.logging_config import logger
from app.core.redis_client import get_redis, is_redis_available

_PREFIX = "revoked_refresh_jti:"
_FALLBACK_REVOKED: set[str] = set()


async def revoke_refresh_token(jti: str, ttl_seconds: int) -> None:
    _FALLBACK_REVOKED.add(jti)
    if not await is_redis_available():
        return
    try:
        await get_redis().set(f"{_PREFIX}{jti}", "1", ex=max(ttl_seconds, 1))
    except Exception as exc:  # pragma: no cover - Redis outage shouldn't hard-fail auth
        logger.warning(f"Could not persist refresh-token revocation, allowing degraded mode: {exc}")


async def is_refresh_token_revoked(jti: str) -> bool:
    if jti in _FALLBACK_REVOKED:
        return True
    if not await is_redis_available():
        return False
    try:
        return bool(await get_redis().exists(f"{_PREFIX}{jti}"))
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Could not check refresh-token revocation status: {exc}")
        return False
