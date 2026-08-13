import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, TimestampMixin, UUIDMixin


class FeedbackRating(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class Feedback(Base, UUIDMixin, TimestampMixin):
    """Thumbs up/down (+ optional comment) on a chat answer, tied back to the source document."""

    __tablename__ = "feedback"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True)
    rating: Mapped[FeedbackRating] = mapped_column(
        Enum(FeedbackRating, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="feedback_entries")
    document = relationship("Document", back_populates="feedback_entries")
