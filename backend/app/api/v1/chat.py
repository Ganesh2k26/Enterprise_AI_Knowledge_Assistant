import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatSessionCreate, ChatSessionRead
from app.services.chat_service import ChatService

router = APIRouter()


@router.get("/sessions", response_model=list[ChatSessionRead])
async def list_sessions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await ChatService(db).list_sessions(user.id)


@router.post("/sessions", response_model=ChatSessionRead, status_code=201)
async def create_session(
    payload: ChatSessionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    return await ChatService(db).create_session(
        user.id, payload.title, [str(d) for d in payload.document_ids]
    )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    session = await ChatService(db).get_session(session_id, user.id)
    return {
        "id": str(session.id),
        "title": session.title,
        "document_ids": session.document_ids,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role.value,
                "content": m.content,
                "citations": m.citations,
                "confidence_score": m.confidence_score,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ],
    }


@router.patch("/sessions/{session_id}/rename")
async def rename_session(
    session_id: uuid.UUID, title: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    session = await ChatService(db).rename_session(session_id, user.id, title)
    return {"id": str(session.id), "title": session.title}


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    await ChatService(db).delete_session(session_id, user.id)


@router.post("/messages")
async def send_message(
    payload: ChatMessageCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Server-Sent Events stream of the assistant's answer. The frontend consumes
    this with fetch + ReadableStream (not EventSource, since EventSource
    doesn't support POST bodies or Authorization headers) to render tokens
    as they arrive.
    """
    service = ChatService(db)

    async def event_stream():
        try:
            async for token in service.stream_answer(payload.session_id, user.id, user.organization_id, payload.message):
                escaped = token.replace("\n", "\\n")
                yield f"data: {escaped}\n\n"
            yield "event: done\ndata: end\n\n"
        except Exception as exc:  # pragma: no cover
            from app.core.logging_config import logger

            logger.error(f"Chat stream failed: {exc}")
            msg = str(exc).replace("\n", "\\n")
            yield f"data: _{msg}_\n\n"
            yield "event: done\ndata: end\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/regenerate")
async def regenerate_message(
    session_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Deletes the last assistant reply and streams a fresh one for the same last user message."""
    service = ChatService(db)

    async def event_stream():
        try:
            async for token in service.regenerate_last(session_id, user.id, user.organization_id):
                escaped = token.replace("\n", "\\n")
                yield f"data: {escaped}\n\n"
            yield "event: done\ndata: end\n\n"
        except Exception as exc:  # pragma: no cover
            from app.core.logging_config import logger

            logger.error(f"Chat regenerate stream failed: {exc}")
            msg = str(exc).replace("\n", "\\n")
            yield f"data: _{msg}_\n\n"
            yield "event: done\ndata: end\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Returns the full conversation as Markdown for client-side download."""
    session = await ChatService(db).get_session(session_id, user.id)
    lines = [f"# {session.title}", ""]
    for m in session.messages:
        speaker = "**You**" if m.role.value == "user" else "**Assistant**"
        lines.append(f"{speaker} ({m.created_at.isoformat()}):")
        lines.append(m.content)
        if m.citations:
            sources = ", ".join(
                c["filename"] + (f" (p.{c['page_number']})" if c.get("page_number") else "") for c in m.citations
            )
            lines.append(f"\n*Sources: {sources}*")
        lines.append("")
    return {"filename": f"{session.title[:40]}.md", "content": "\n".join(lines)}
