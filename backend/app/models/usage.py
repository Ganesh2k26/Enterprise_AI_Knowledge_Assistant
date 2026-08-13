import uuid

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, GUID, TimestampMixin, UUIDMixin


class UsageLog(Base, UUIDMixin, TimestampMixin):
    """One row per LLM/embedding call, for the admin dashboard's usage/cost charts."""

    __tablename__ = "usage_logs"
    __table_args__ = (Index("ix_usage_logs_org_created", "organization_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(50), index=True)  # "chat", "embedding", "upload", "ocr"
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
