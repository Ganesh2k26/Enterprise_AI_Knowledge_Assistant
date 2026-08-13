"""
Declarative base + shared mixins (UUID PK, timestamps) used by every model.

MySQL has no native UUID column type (unlike Postgres), so UUIDs are stored
as CHAR(36) strings. A GUID TypeDecorator keeps every model's `id` typed as
`uuid.UUID` in Python while storing a plain string in MySQL.
"""
import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent UUID column, stored as CHAR(36) in MySQL."""

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(str(value))


class Base(DeclarativeBase):
    pass


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
