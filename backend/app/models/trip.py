from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SafeTripStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class SafeTrip(Base):
    """Persisted Safe Trip route snapshot and lifecycle state."""

    __tablename__ = "safe_trips"
    __table_args__ = (
        CheckConstraint("origin_latitude >= -90 AND origin_latitude <= 90", name="ck_safe_trips_origin_latitude"),
        CheckConstraint("origin_longitude >= -180 AND origin_longitude <= 180", name="ck_safe_trips_origin_longitude"),
        CheckConstraint("destination_latitude >= -90 AND destination_latitude <= 90", name="ck_safe_trips_destination_latitude"),
        CheckConstraint("destination_longitude >= -180 AND destination_longitude <= 180", name="ck_safe_trips_destination_longitude"),
        CheckConstraint("route_distance_meters >= 0", name="ck_safe_trips_route_distance"),
        CheckConstraint("route_duration_seconds >= 0", name="ck_safe_trips_route_duration"),
        CheckConstraint(
            "status IN ('planned', 'active', 'completed')",
            name="ck_safe_trips_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    selected_route_id: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    origin_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    destination_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    route_distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    route_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    route_geometry: Mapped[list[dict[str, float]]] = mapped_column(JSONB, nullable=False)
    expected_arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SafeTripStatus.PLANNED.value, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SafeTripLocation(Base):
    """A single user-provided location update for an active Safe Trip."""

    __tablename__ = "safe_trip_locations"
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_safe_trip_locations_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_safe_trip_locations_longitude"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    trip_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("safe_trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SafeTripCheckIn(Base):
    """An explicit user check-in recorded during an active Safe Trip."""

    __tablename__ = "safe_trip_check_ins"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    trip_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("safe_trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
