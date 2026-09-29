from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TrustedContactMethod(StrEnum):
    PHONE = "phone"
    EMAIL = "email"


class TrustedContact(Base):
    """A user-managed contact reserved for future notification workflows."""

    __tablename__ = "trusted_contacts"
    __table_args__ = (
        CheckConstraint("contact_method IN ('phone', 'email')", name="ck_trusted_contacts_method"),
        CheckConstraint("length(trim(name)) > 0", name="ck_trusted_contacts_name"),
        CheckConstraint("length(trim(contact_value)) > 0", name="ck_trusted_contacts_value"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_method: Mapped[str] = mapped_column(String(16), nullable=False)
    contact_value: Mapped[str] = mapped_column(String(320), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
