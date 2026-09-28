from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.incident import (
    ConfidenceLevel,
    IncidentCategory,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)


class IncidentReportCreate(BaseModel):
    category: IncidentCategory
    description: str = Field(min_length=10, max_length=2000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    occurred_at: datetime | None = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM

    @field_validator("description")
    @classmethod
    def description_must_contain_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 10:
            raise ValueError("description must contain at least 10 non-whitespace characters")
        return normalized

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_cannot_be_in_the_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        if value > datetime.now(timezone.utc):
            raise ValueError("occurred_at cannot be in the future")
        return value


class ConfidenceDetails(BaseModel):
    level: ConfidenceLevel
    corroboration_count: int = Field(ge=0)
    factors: list[str]


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: IncidentCategory
    description: str
    latitude: float
    longitude: float
    occurred_at: datetime
    reported_at: datetime
    severity: IncidentSeverity
    source: IncidentSource
    status: IncidentStatus
    confidence: ConfidenceDetails
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    limit: int
    count: int


class IncidentSignalContext(BaseModel):
    """Database-independent incident input for a future safety engine."""

    latitude: float
    longitude: float
    radius_meters: float
    as_of: datetime
    incident_count: int
    recent_incident_count: int
    severity_counts: dict[str, int]
    category_counts: dict[str, int]
    confidence_level_counts: dict[str, int]
    indicator_notes: list[str]
