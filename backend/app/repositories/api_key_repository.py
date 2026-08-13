import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    def __init__(self, db: AsyncSession):
        super().__init__(APIKey, db)

    async def list_for_user(self, user_id: uuid.UUID) -> list[APIKey]:
        result = await self.db.execute(select(APIKey).where(APIKey.user_id == user_id))
        return list(result.scalars().all())
