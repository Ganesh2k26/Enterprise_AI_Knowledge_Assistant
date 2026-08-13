"""Shared FastAPI dependencies: DB session passthrough + current-user resolution."""
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


async def get_current_user(
    authorization: str = Header(default=""), db: AsyncSession = Depends(get_db)
) -> User:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header.")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired access token.")

    user = await UserRepository(db).get(payload["sub"])
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("owner", "admin") and not user.is_superuser:
        raise UnauthorizedError("Admin privileges required.")
    return user
