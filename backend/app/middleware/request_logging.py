"""Logs method/path/status/duration for every request -- feeds Prometheus/OTel style metrics."""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_config import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
        )
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
