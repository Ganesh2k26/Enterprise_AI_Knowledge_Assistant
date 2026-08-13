import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentRead, DocumentUpdate
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    folder_id: uuid.UUID | None = None,
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await DocumentRepository(db).list_for_org(user.organization_id, folder_id, search)


@router.post("/upload", response_model=DocumentRead, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    return await service.upload_and_process(file, user.id, user.organization_id, folder_id)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    doc = await DocumentRepository(db).get(document_id)
    if not doc or doc.organization_id != user.organization_id:
        raise NotFoundError("Document not found.")
    return doc


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = DocumentRepository(db)
    doc = await repo.get(document_id)
    if not doc or doc.organization_id != user.organization_id:
        raise NotFoundError("Document not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    return await repo.commit_refresh(doc)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await DocumentService(db).delete_document(document_id, user.organization_id)
