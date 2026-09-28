from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncidentCategory(StrEnum):
    HARASSMENT = "harassment"
    THEFT = "theft"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    POOR_LIGHTING = "poor_lighting"
    UNSAFE_ISOLATED_AREA = "unsafe_isolated_area"
    OTHER = "other"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IncidentSource(StrEnum):
    COMMUNITY_REPORT = "community_report"
    OFFICIAL_REPORT = "official_report"
    VERIFIED_PARTNER = "verified_partner"
    IMPORTED_DATA = "imported_data"


class IncidentStatus(StrEnum):
    UNVERIFIED = "unverified"
    CORROBORATED = "corroborated"
    VALIDATED = "validated"
    REJECTED = "rejected"


class ConfidenceLevel(StrEnum):
    UNVERIFIED = "unverified"
    CORROBORATED = "corroborated"
    HIGHER_CONFIDENCE = "higher_confidence"


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_incidents_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_incidents_longitude"),
        CheckConstraint("corroboration_count >= 0", name="ck_incidents_corroboration_count"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    category: Mapped[IncidentCategory] = mapped_column(
        ENUM(IncidentCategory, name="incident_category", create_type=False), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    location: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        ENUM(IncidentSeverity, name="incident_severity", create_type=False), nullable=False, index=True
    )
    source: Mapped[IncidentSource] = mapped_column(
        ENUM(IncidentSource, name="incident_source", create_type=False), nullable=False, index=True
    )
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        ENUM(ConfidenceLevel, name="confidence_level", create_type=False), nullable=False, index=True
    )
    corroboration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[IncidentStatus] = mapped_column(
        ENUM(IncidentStatus, name="incident_status", create_type=False), nullable=False, index=True
    )
    confidence_factors: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
