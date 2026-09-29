from enum import StrEnum

from pydantic import BaseModel, Field


class SafePlaceCategory(StrEnum):
    HOSPITAL = "hospital"
    POLICE_STATION = "police_station"
    PETROL_PUMP = "petrol_pump"
    HOTEL = "hotel"
    OPEN_BUSINESS = "open_business"
    ASSISTANCE = "assistance"


class SafePlaceResponse(BaseModel):
    id: str
    name: str
    category: SafePlaceCategory
    latitude: float
    longitude: float
    distance_meters: float
    is_demo_resource: bool = True


class SafePlaceListResponse(BaseModel):
    resources: list[SafePlaceResponse]
    count: int
    disclaimer: str


class NearbySafePlaceQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius: float = Field(default=5000, gt=0, le=50000)
    category: SafePlaceCategory | None = None
