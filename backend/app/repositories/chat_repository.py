import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatSession
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatSession, db)

    async def list_for_user(self, user_id: uuid.UUID) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_messages(self, session_id: uuid.UUID) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id).options(selectinload(ChatSession.messages))
        )
        return result.scalar_one_or_none()

    async def add_message(self, **kwargs) -> ChatMessage:
        msg = ChatMessage(**kwargs)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg
