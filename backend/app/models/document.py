import enum
import uuid

from sqlalchemy import BigInteger, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, TimestampMixin, UUIDMixin


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Folder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "folders"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_folder_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True
    )

    documents = relationship("Document", back_populates="folder")
    children = relationship("Folder", cascade="all, delete-orphan")


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_org_status", "organization_id", "status"),)

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=DocumentStatus.PENDING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    is_favorite: Mapped[bool] = mapped_column(default=False)
    is_scanned: Mapped[bool] = mapped_column(default=False)  # true if OCR was used to extract text
    embedding_count: Mapped[int] = mapped_column(default=0)

    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True
    )

    owner = relationship("User", back_populates="documents")
    organization = relationship("Organization", back_populates="documents")
    folder = relationship("Folder", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    feedback_entries = relationship("Feedback", back_populates="document", cascade="all, delete-orphan")
