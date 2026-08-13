import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, GUID, TimestampMixin, UUIDMixin


class OrgSetting(Base, UUIDMixin, TimestampMixin):
    """Generic per-organization key/value settings (e.g. default chunk size, theme)."""

    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)

    organization = relationship("Organization", back_populates="settings")
