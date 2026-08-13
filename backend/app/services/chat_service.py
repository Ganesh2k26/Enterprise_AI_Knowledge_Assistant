"""
Orchestrates a RAG chat turn: retrieve -> build grounded prompt -> stream
generation -> persist both the user message and assistant reply (with
citations + suggested follow-ups) once streaming completes.
"""
import time
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.llm.factory import get_llm_provider
from app.models.chat import ChatMessage, MessageRole
from app.models.usage import UsageLog
from app.rag.prompt_builder import average_confidence, build_citations, build_system_prompt
from app.rag.retriever import retrieve
from app.repositories.chat_repository import ChatRepository

MAX_HISTORY_TURNS = 6


def _suggest_follow_ups(citations: list[dict]) -> list[str]:
    """Heuristic suggested-question generator from retrieved section titles -- no extra LLM call needed."""
    suggestions = []
    seen_docs = set()
    for c in citations:
        if c["document_id"] in seen_docs:
            continue
        seen_docs.add(c["document_id"])
        topic = c.get("section_title") or c["filename"]
        suggestions.append(f"Can you summarize the key points about {topic}?")
        if len(suggestions) >= 3:
            break
    return suggestions


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChatRepository(db)
        self.llm = get_llm_provider()

    async def create_session(self, user_id: uuid.UUID, title: str, document_ids: list[str]):
        return await self.repo.create(user_id=user_id, title=title, document_ids=document_ids)

    async def _generate_and_persist(
        self,
        session,
        organization_id: uuid.UUID,
        user_message_text: str,
        history_override: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        start = time.perf_counter()
        chunks = await retrieve(
            query=user_message_text,
            organization_id=str(organization_id),
            document_ids=session.document_ids or None,
        )
        system_prompt = build_system_prompt(chunks)
        citations = build_citations(chunks)
        confidence = average_confidence(chunks)

        history = history_override
        if history is None:
            history = [
                {"role": "user" if m.role == MessageRole.USER else "model", "text": m.content}
                for m in session.messages[-MAX_HISTORY_TURNS:]
            ]

        full_response = ""
        async for token in self.llm.stream_chat(system_prompt, history, user_message_text):
            full_response += token
            yield token

        suggestions = _suggest_follow_ups(citations)
        await self.repo.add_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            citations=citations,
            confidence_score=confidence,
            token_usage={"suggested_questions": suggestions},
        )
        session.title = session.title if session.title != "New Chat" else user_message_text[:60]
        self.db.add(
            UsageLog(
                user_id=session.user_id,
                organization_id=organization_id,
                action="chat",
                completion_tokens=len(full_response.split()),
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        )
        await self.db.commit()

    async def stream_answer(
        self, session_id: uuid.UUID, user_id: uuid.UUID, organization_id: uuid.UUID, message: str
    ) -> AsyncGenerator[str, None]:
        session = await self.repo.get_with_messages(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session not found.")

        await self.repo.add_message(session_id=session_id, role=MessageRole.USER, content=message)
        async for token in self._generate_and_persist(session, organization_id, message):
            yield token

    async def regenerate_last(
        self, session_id: uuid.UUID, user_id: uuid.UUID, organization_id: uuid.UUID
    ) -> AsyncGenerator[str, None]:
        """Removes the last assistant reply (if any) and re-generates it from the same last user message."""
        session = await self.repo.get_with_messages(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session not found.")
        if not session.messages:
            raise ValidationAppError("This chat has no messages to regenerate.")

        last_user_message = None
        for m in reversed(session.messages):
            if m.role == MessageRole.ASSISTANT:
                await self.db.delete(m)
            elif m.role == MessageRole.USER:
                last_user_message = m.content
                break
        await self.db.commit()

        if not last_user_message:
            raise ValidationAppError("No previous user message found to regenerate from.")

        session = await self.repo.get_with_messages(session_id)
        async for token in self._generate_and_persist(session, organization_id, last_user_message):
            yield token

    async def list_sessions(self, user_id: uuid.UUID):
        return await self.repo.list_for_user(user_id)

    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID):
        session = await self.repo.get_with_messages(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session not found.")
        return session

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> None:
        session = await self.get_session(session_id, user_id)
        await self.repo.delete(session)

    async def rename_session(self, session_id: uuid.UUID, user_id: uuid.UUID, title: str):
        session = await self.get_session(session_id, user_id)
        session.title = title
        return await self.repo.commit_refresh(session)
