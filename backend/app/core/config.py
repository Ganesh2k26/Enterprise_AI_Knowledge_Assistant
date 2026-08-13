"""
Centralized application settings loaded from environment variables.
Uses pydantic-settings so every config value is typed and validated at
process startup instead of failing deep inside a request handler.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env next to the backend package root so uvicorn reload / cwd shifts
# cannot silently drop GEMINI_API_KEY and other secrets.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Enterprise AI Knowledge Assistant"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str = Field(default="change-me-in-prod-please-use-a-long-random-string")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MIN_PASSWORD_LENGTH: int = 8
    SECURE_COOKIES: bool = False  # set true behind HTTPS in production

    # --- Database ---
    # Default to SQLite for local development so the app runs out of the box without
    # a separate MySQL service. Override with DATABASE_URL when a real DB is available.
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./app.db")
    # Alembic runs migrations synchronously; derived automatically in alembic/env.py
    # from DATABASE_URL by swapping the aiomysql driver for pymysql.

    # --- Redis (rate limiting / caching) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # --- LLM provider abstraction (generation only) ---
    LLM_PROVIDER: str = "gemini"  # pluggable via app/llm/factory.py
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key (free tier)")
    GEMINI_CHAT_MODEL: str = "gemini-flash-latest"

    # --- Local embeddings (SentenceTransformers, no paid API) ---
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSIONS: int = 384
    EMBEDDING_DEVICE: str = "cpu"

    # --- Vector store (ChromaDB) ---
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_PREFIX: str = "org"

    # --- OCR ---
    OCR_ENABLED: bool = True
    OCR_LANGUAGES: List[str] = ["en"]
    OCR_MIN_TEXT_CHARS_PER_PAGE: int = 20  # below this, a PDF page is treated as scanned

    # --- File storage ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg",
    ]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "image/png",
        "image/jpeg",
    ]

    # --- RAG tuning ---
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 80
    TOP_K_RESULTS: int = 5
    OVER_FETCH_MULTIPLIER: int = 4
    SIMILARITY_THRESHOLD: float = 0.3
    LEXICAL_WEIGHT: float = 0.2
    SEMANTIC_WEIGHT: float = 0.8
    DEDUP_SIMILARITY_THRESHOLD: float = 0.92
    MAX_CONTEXT_TOKENS: int = 3000

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("CORS_ORIGINS", "ALLOWED_EXTENSIONS", "ALLOWED_MIME_TYPES", "OCR_LANGUAGES", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def _validate_environment(self) -> "Settings":
        """Fail fast at startup instead of deep inside a request handler."""
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY.startswith("change-me"):
                raise ValueError("SECRET_KEY must be set to a real secret in production.")
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production.")
        if self.LLM_PROVIDER not in ("gemini",):
            raise ValueError(f"Unsupported LLM_PROVIDER '{self.LLM_PROVIDER}'.")
        if not self.DATABASE_URL:
            self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse the environment exactly once per process."""
    return Settings()


settings = get_settings()
