from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SafeTripStatus(StrEnum):
    PLANNED = "planned"


class SafeTrip(Base):
    """Persisted Safe Trip plan; monitoring lifecycle is implemented later."""

    __tablename__ = "safe_trips"
    __table_args__ = (
        CheckConstraint("origin_latitude >= -90 AND origin_latitude <= 90", name="ck_safe_trips_origin_latitude"),
        CheckConstraint("origin_longitude >= -180 AND origin_longitude <= 180", name="ck_safe_trips_origin_longitude"),
        CheckConstraint("destination_latitude >= -90 AND destination_latitude <= 90", name="ck_safe_trips_destination_latitude"),
        CheckConstraint("destination_longitude >= -180 AND destination_longitude <= 180", name="ck_safe_trips_destination_longitude"),
        CheckConstraint("route_distance_meters >= 0", name="ck_safe_trips_route_distance"),
        CheckConstraint("route_duration_seconds >= 0", name="ck_safe_trips_route_duration"),
        CheckConstraint("status = 'planned'", name="ck_safe_trips_status"),
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
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SafeTripStatus.PLANNED.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

