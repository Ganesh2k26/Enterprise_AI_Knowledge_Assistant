import uuid

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    message_id: uuid.UUID
    document_id: uuid.UUID | None = None
    rating: str  # "up" | "down"
    comment: str | None = None
