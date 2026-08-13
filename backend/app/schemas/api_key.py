import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class APIKeyCreate(BaseModel):
    name: str


class APIKeyCreated(BaseModel):
    """Returned exactly once, at creation time -- the plaintext key is never stored or shown again."""

    id: uuid.UUID
    name: str
    plaintext_key: str
    key_prefix: str


class APIKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
