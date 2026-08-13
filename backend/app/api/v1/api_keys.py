import secrets
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.database.session import get_db
from app.models.user import User
from app.repositories.api_key_repository import APIKeyRepository
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyRead

router = APIRouter()


@router.get("", response_model=list[APIKeyRead])
async def list_api_keys(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await APIKeyRepository(db).list_for_user(user.id)


@router.post("", response_model=APIKeyCreated, status_code=201)
async def create_api_key(
    payload: APIKeyCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    plaintext = f"atlas_{secrets.token_urlsafe(32)}"
    prefix = plaintext[:12]
    key = await APIKeyRepository(db).create(
        user_id=user.id, name=payload.name, key_prefix=prefix, hashed_key=hash_password(plaintext)
    )
    return APIKeyCreated(id=key.id, name=key.name, plaintext_key=plaintext, key_prefix=prefix)


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(key_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = APIKeyRepository(db)
    key = await repo.get(key_id)
    if not key or key.user_id != user.id:
        raise NotFoundError("API key not found.")
    await repo.delete(key)
