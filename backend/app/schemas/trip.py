from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.routes import Coordinate, RouteGeometry


class SafeTripCreate(BaseModel):
    selected_route_id: str = Field(min_length=1, max_length=255)
    origin: Coordinate
    destination: Coordinate
    distance_meters: float = Field(ge=0)
    estimated_duration_seconds: int = Field(ge=0)
    geometry: RouteGeometry
    expected_arrival_at: datetime

    @field_validator("expected_arrival_at")
    @classmethod
    def expected_arrival_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("expected_arrival_at must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def route_endpoints_must_match_snapshot(self):
        if self.geometry.coordinates[0] != self.origin or self.geometry.coordinates[-1] != self.destination:
            raise ValueError("route geometry endpoints must match origin and destination")
        return self


class SafeTripResponse(BaseModel):
    id: UUID
    selected_route_id: str
    origin: Coordinate
    destination: Coordinate
    distance_meters: float
    estimated_duration_seconds: int
    geometry: RouteGeometry
    expected_arrival_at: datetime
    status: str
    created_at: datetime

