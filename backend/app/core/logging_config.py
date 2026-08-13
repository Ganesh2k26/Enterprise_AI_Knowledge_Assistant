"""Structured JSON logging so logs are easy to ship to ELK / Loki / CloudWatch."""
import logging
import sys

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    for noisy in ("uvicorn.access", "httpx", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


logger = logging.getLogger("app")
