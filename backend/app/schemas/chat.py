import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    title: str = "New Chat"
    document_ids: list[uuid.UUID] = Field(default_factory=list)


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    document_ids: list[str]
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int | None = None
    chunk_text: str
    similarity_score: float


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict]
    confidence_score: float | None
    created_at: datetime


class ChatMessageCreate(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=8000)
