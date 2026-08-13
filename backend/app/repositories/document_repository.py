import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, Folder
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def list_for_org(
        self, organization_id: uuid.UUID, folder_id: uuid.UUID | None = None, search: str | None = None
    ) -> list[Document]:
        query = select(Document).where(Document.organization_id == organization_id)
        if folder_id:
            query = query.where(Document.folder_id == folder_id)
        if search:
            query = query.where(Document.filename.ilike(f"%{search}%"))
        query = query.order_by(Document.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())


class FolderRepository(BaseRepository[Folder]):
    def __init__(self, db: AsyncSession):
        super().__init__(Folder, db)

    async def list_for_owner(self, owner_id: uuid.UUID) -> list[Folder]:
        result = await self.db.execute(select(Folder).where(Folder.owner_id == owner_id))
        return list(result.scalars().all())
