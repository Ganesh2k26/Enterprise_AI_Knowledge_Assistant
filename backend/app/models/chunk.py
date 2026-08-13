import uuid

from sqlalchemy import ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, TimestampMixin, UUIDMixin


class Chunk(Base, UUIDMixin, TimestampMixin):
    """
    Metadata row for a chunk. The actual embedding vector lives in ChromaDB;
    this table is the source of truth for text + citation metadata (MySQL
    stays queryable/joinable while Chroma stays purely for ANN search).

    `parent_chunk_id` supports parent-document retrieval: small chunks are
    embedded/searched for precision, but the parent (a larger surrounding
    block, e.g. the full page) can be pulled in for generation context.
    """

    __tablename__ = "chunks"
    __table_args__ = (Index("ix_chunks_document_index", "document_id", "chunk_index"),)

    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    parent_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    vector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    document = relationship("Document", back_populates="chunks")
