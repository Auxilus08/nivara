from enum import StrEnum
from math import isfinite

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.safety import SafetyAssessment


class Coordinate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("latitude", "longitude")
    @classmethod
    def coordinate_must_be_finite(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("coordinate must be finite")
        return value


class RouteMode(StrEnum):
    FASTEST = "fastest"
    BALANCED = "balanced"
    SAFETY_PRIORITY = "safety_priority"


class RouteGeometry(BaseModel):
    """Provider-neutral route geometry represented as latitude/longitude points."""

    coordinates: list[Coordinate] = Field(min_length=2)


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    mode: RouteMode = RouteMode.FASTEST

    @model_validator(mode="after")
    def origin_and_destination_must_differ(self):
        if self.origin == self.destination:
            raise ValueError("origin and destination must be different")
        return self


class RouteCandidate(BaseModel):
    route_id: str
    origin: Coordinate
    destination: Coordinate
    distance_meters: float = Field(ge=0)
    estimated_duration_seconds: int = Field(ge=0)
    geometry: RouteGeometry | None = None
    provider: str
    provider_metadata: dict[str, str] = Field(default_factory=dict)
    safety_assessment: SafetyAssessment | None = None
    normalized_travel_score: float | None = Field(default=None, ge=0, le=100)
    comparison_cost: float | None = Field(default=None, ge=0)
    comparison_explanation: str | None = None


class RouteResponse(BaseModel):
    mode: RouteMode
    routes: list[RouteCandidate]
    selected_route_id: str | None = None
    comparison_explanation: str = (
        "Route selection is based on the configured objective and available data; "
        "it is not a guarantee of safety."
    )


class DestinationSuggestion(BaseModel):
    """Provider-neutral future geocoding/search result."""

    suggestion_id: str
    label: str
    coordinate: Coordinate
