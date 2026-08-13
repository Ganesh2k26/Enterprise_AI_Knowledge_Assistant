"""Domain-level exceptions. Translated to HTTP responses in middleware/error_handler.py."""


class AppException(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    status_code = 404


class UnauthorizedError(AppException):
    status_code = 401


class ForbiddenError(AppException):
    status_code = 403


class ConflictError(AppException):
    status_code = 409


class ValidationAppError(AppException):
    status_code = 422


class RateLimitExceeded(AppException):
    status_code = 429
