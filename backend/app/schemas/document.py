import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FolderCreate(BaseModel):
    name: str
    parent_folder_id: uuid.UUID | None = None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None
    created_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    page_count: int | None
    is_favorite: bool
    is_scanned: bool
    embedding_count: int
    folder_id: uuid.UUID | None
    created_at: datetime


class DocumentUpdate(BaseModel):
    is_favorite: bool | None = None
    folder_id: uuid.UUID | None = None
