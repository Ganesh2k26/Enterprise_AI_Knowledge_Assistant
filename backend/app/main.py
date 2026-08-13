"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging, logger
from app.database.init_db import ensure_directories, init_database
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.rag.embeddings import warmup_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    ensure_directories()
    await init_database()
    warmup_embedding_model()
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise-grade RAG platform: chat with your documents.",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

register_error_handlers(app)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}
