import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    def __init__(self, db: AsyncSession):
        super().__init__(Feedback, db)

    async def list_for_message(self, message_id: uuid.UUID) -> list[Feedback]:
        result = await self.db.execute(select(Feedback).where(Feedback.message_id == message_id))
        return list(result.scalars().all())
