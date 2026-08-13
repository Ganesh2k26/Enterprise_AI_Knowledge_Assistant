"""Global exception handlers -- turns domain exceptions into clean JSON errors."""
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.logging_config import logger


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Validation error", "errors": exc.errors()})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        error_id = str(uuid.uuid4())
        logger.error(f"Unhandled exception [{error_id}]: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred.", "error_id": error_id},
        )
