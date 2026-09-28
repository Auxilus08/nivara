from pydantic import BaseModel, Field, model_validator

from app.services.safety import AssessmentConfidence, RiskLevel


class HeatmapQuery(BaseModel):
    min_latitude: float = Field(ge=-90, le=90)
    min_longitude: float = Field(ge=-180, le=180)
    max_latitude: float = Field(ge=-90, le=90)
    max_longitude: float = Field(ge=-180, le=180)
    rows: int = Field(default=8, ge=2, le=12)
    columns: int = Field(default=8, ge=2, le=12)

    @model_validator(mode="after")
    def validate_bounded_viewport(self):
        latitude_span = self.max_latitude - self.min_latitude
        longitude_span = self.max_longitude - self.min_longitude
        if latitude_span <= 0 or longitude_span <= 0:
            raise ValueError("heatmap bounds must have increasing minimum and maximum coordinates")
        if latitude_span > 2 or longitude_span > 2:
            raise ValueError("heatmap bounds are too large; request a smaller viewport")
        if latitude_span < 0.02 or longitude_span < 0.02:
            raise ValueError("heatmap bounds are too small to preserve contextual location privacy")
        return self


class HeatmapBounds(BaseModel):
    min_latitude: float
    min_longitude: float
    max_latitude: float
    max_longitude: float


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    incident_count: int = Field(ge=0)
    confidence: AssessmentConfidence


class HeatmapResponse(BaseModel):
    bounds: HeatmapBounds
    rows: int
    columns: int
    points: list[HeatmapPoint]
    incident_count: int = Field(ge=0)
    disclaimer: str
