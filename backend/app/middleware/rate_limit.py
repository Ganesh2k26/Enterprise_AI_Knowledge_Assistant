"""
Sliding-window rate limiter backed by Redis. Falls back to allowing all
requests if Redis is unreachable, so a Redis outage degrades gracefully
instead of taking the whole API down.
"""
import time

import redis.asyncio as redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import logger

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health") or request.url.path.startswith("/docs"):
            return await call_next(request)

        client_id = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_id}:{int(time.time() // 60)}"

        try:
            count = await _redis.incr(key)
            if count == 1:
                await _redis.expire(key, 60)
            if count > settings.RATE_LIMIT_PER_MINUTE:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again shortly."})
        except Exception as exc:
            logger.warning(f"Rate limiter unavailable, allowing request: {exc}")

        return await call_next(request)
