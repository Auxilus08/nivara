from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class EmergencyCreate(BaseModel):
    trip_id: UUID | None = None
    emergency_type: str = Field(default="sos", min_length=1, max_length=64)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordinates_must_be_provided_together(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class EmergencyResponse(BaseModel):
    id: UUID
    trip_id: UUID | None
    status: str
    emergency_type: str
    latitude: float | None
    longitude: float | None
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    notification_mode: str = "mock_demo_only"
    sharing_status: str = "sharing_disabled"


class EmergencyResource(BaseModel):
    id: str
    category: str
    name: str
    description: str
    is_demo_resource: bool = True


class EmergencyResourceListResponse(BaseModel):
    resources: list[EmergencyResource]
    count: int
    disclaimer: str
