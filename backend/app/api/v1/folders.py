import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.document_repository import FolderRepository
from app.schemas.document import FolderCreate, FolderRead

router = APIRouter()


@router.get("", response_model=list[FolderRead])
async def list_folders(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Flat list; the frontend assembles the tree client-side from parent_folder_id."""
    return await FolderRepository(db).list_for_owner(user.id)


@router.post("", response_model=FolderRead, status_code=201)
async def create_folder(
    payload: FolderCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    return await FolderRepository(db).create(
        name=payload.name, owner_id=user.id, parent_folder_id=payload.parent_folder_id
    )


@router.delete("/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    repo = FolderRepository(db)
    folder = await repo.get(folder_id)
    if folder and folder.owner_id == user.id:
        await repo.delete(folder)
