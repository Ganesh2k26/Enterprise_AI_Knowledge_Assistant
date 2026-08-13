"""
Password hashing and JWT issuing/verification.
Kept dependency-free of FastAPI so it's trivially unit-testable.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=12000,
)

PASSWORD_RULES = (
    (r".{8,}", "at least 8 characters"),
    (r"[A-Z]", "an uppercase letter"),
    (r"[a-z]", "a lowercase letter"),
    (r"\d", "a digit"),
    (r"[^A-Za-z0-9]", "a special character"),
)


def validate_password_strength(password: str) -> list[str]:
    """Returns a list of unmet rule descriptions; empty list means the password is strong enough."""
    return [desc for pattern, desc in PASSWORD_RULES if not re.search(pattern, password)]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> tuple[str, str]:
    """Returns (encoded_jwt, jti) so callers can track/rotate/blacklist refresh tokens."""
    now = datetime.now(timezone.utc)
    jti = str(uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def create_access_token(subject: str) -> str:
    token, _ = _create_token(subject, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    return token


def create_refresh_token(subject: str) -> tuple[str, str]:
    """Returns (token, jti). The jti is stored/rotated via app.core.token_blacklist."""
    return _create_token(subject, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
