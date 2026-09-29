from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SafeTripTrustedContact(Base):
    """Association between a Safe Trip and a selected active trusted contact."""

    __tablename__ = "safe_trip_trusted_contacts"
    __table_args__ = (
        PrimaryKeyConstraint("safe_trip_id", "trusted_contact_id", name="pk_safe_trip_trusted_contacts"),
    )

    safe_trip_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("safe_trips.id", ondelete="CASCADE"), nullable=False
    )
    trusted_contact_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("trusted_contacts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
