"""
Orchestrates the ingestion pipeline: validate -> save file -> extract text
(with OCR fallback) -> parent/child chunk -> embed locally -> store in
Chroma + MySQL. Runs inline (async) for simplicity; in a production
deployment this would be dispatched to a Celery worker so uploads don't
block the request thread -- see workers/README.md.
"""
import time
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging_config import logger
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.usage import UsageLog
from app.rag.chunking import chunk_pages
from app.rag.embeddings import embed_texts
from app.rag.loaders import load_document
from app.rag.vectorstore import VectorStore
from app.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DocumentRepository(db)

    def _validate_upload(self, file: UploadFile) -> str:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValidationAppError(
                f"File type '{ext or 'unknown'}' is not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        # Best-effort MIME check against the client-reported content type. This is not a
        # substitute for content sniffing, but catches obviously mislabeled uploads cheaply
        # without adding a native libmagic dependency to the container image.
        if file.content_type and file.content_type not in settings.ALLOWED_MIME_TYPES:
            logger.warning(f"Upload '{file.filename}' has unexpected content-type '{file.content_type}'")
        return ext

    async def upload_and_process(
        self, file: UploadFile, owner_id: uuid.UUID, organization_id: uuid.UUID, folder_id: uuid.UUID | None
    ) -> Document:
        ext = self._validate_upload(file)

        upload_dir = Path(settings.UPLOAD_DIR) / str(organization_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4()}{ext}"
        dest_path = upload_dir / stored_name

        size = 0
        with open(dest_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    dest_path.unlink(missing_ok=True)
                    raise ValidationAppError(f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.")
                out.write(chunk)
        if size == 0:
            dest_path.unlink(missing_ok=True)
            raise ValidationAppError("Uploaded file is empty.")

        document = await self.repo.create(
            filename=file.filename,
            file_type=ext,
            file_size_bytes=size,
            storage_path=str(dest_path),
            status=DocumentStatus.PROCESSING,
            owner_id=owner_id,
            organization_id=organization_id,
            folder_id=folder_id,
        )

        try:
            await self._process_document(document)
        except Exception as exc:
            logger.error(f"Document processing failed for {document.id}: {exc}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)
            await self.repo.commit_refresh(document)
        return document

    async def _process_document(self, document: Document) -> None:
        start = time.perf_counter()
        pages, used_ocr = load_document(document.storage_path, document.file_type)
        text_chunks = chunk_pages(pages)
        if not text_chunks:
            raise ValidationAppError("Document produced no usable text chunks.")

        # Persist one parent Chunk row per distinct parent block (parent_chunk_id=None,
        # not embedded/searched directly -- it exists purely to give child chunks a home
        # for parent-document retrieval context).
        parent_ids: dict[int, uuid.UUID] = {}
        for parent_index in sorted({c.parent_index for c in text_chunks}):
            parent_text = next(c.parent_content for c in text_chunks if c.parent_index == parent_index)
            parent_row = Chunk(
                document_id=document.id,
                content=parent_text,
                chunk_index=-1,
                page_number=next((c.page_number for c in text_chunks if c.parent_index == parent_index), None),
                token_count=0,
                vector_id=f"parent_{document.id}_{parent_index}",
            )
            self.db.add(parent_row)
            await self.db.flush()
            parent_ids[parent_index] = parent_row.id

        # Child chunks: these are what gets embedded and searched.
        child_ids = [uuid.uuid4() for _ in text_chunks]
        embeddings = await embed_texts([c.content for c in text_chunks])

        store = VectorStore(str(document.organization_id))
        store.add(
            ids=[str(cid) for cid in child_ids],
            embeddings=embeddings,
            documents=[c.content for c in text_chunks],
            metadatas=[
                {
                    "document_id": str(document.id),
                    "filename": document.filename,
                    "page_number": c.page_number or 0,
                    "chunk_index": c.chunk_index,
                    "section_title": c.section_title or "",
                    "parent_content": c.parent_content,
                }
                for c in text_chunks
            ],
        )

        for c, child_id in zip(text_chunks, child_ids):
            self.db.add(
                Chunk(
                    id=child_id,
                    document_id=document.id,
                    parent_chunk_id=parent_ids[c.parent_index],
                    content=c.content,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    token_count=c.token_count,
                    vector_id=str(child_id),
                    chunk_metadata={"section_title": c.section_title} if c.section_title else {},
                )
            )

        document.status = DocumentStatus.READY
        document.page_count = max((p[1] or 0 for p in pages), default=None)
        document.is_scanned = used_ocr
        document.embedding_count = len(text_chunks)
        await self.db.commit()

        self.db.add(
            UsageLog(
                user_id=document.owner_id,
                organization_id=document.organization_id,
                action="ocr" if used_ocr else "embedding",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        )
        await self.db.commit()

    async def delete_document(self, document_id: uuid.UUID, organization_id: uuid.UUID) -> None:
        document = await self.repo.get(document_id)
        if not document or document.organization_id != organization_id:
            raise NotFoundError("Document not found.")
        VectorStore(str(organization_id)).delete_by_document(str(document_id))
        Path(document.storage_path).unlink(missing_ok=True)
        await self.repo.delete(document)
