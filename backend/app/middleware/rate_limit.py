"""
Sliding-window rate limiter backed by Redis. Falls back to an in-memory
counter when Redis is unreachable so local dev stays fast without a Redis
service running.
"""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.redis_client import get_redis, is_redis_available

_local_counts: dict[str, int] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health") or request.url.path.startswith("/docs"):
            return await call_next(request)
        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        client_id = request.client.host if request.client else "unknown"
        bucket = int(time.time() // 60)
        key = f"ratelimit:{client_id}:{bucket}"

        if await is_redis_available():
            try:
                redis = get_redis()
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, 60)
            except Exception:
                count = _local_counts.get(key, 0) + 1
                _local_counts[key] = count
        else:
            count = _local_counts.get(key, 0) + 1
            _local_counts[key] = count
            if len(_local_counts) > 500:
                _local_counts.clear()

        if count > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again shortly."})

        return await call_next(request)
