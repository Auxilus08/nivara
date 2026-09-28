from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import pi

from pydantic import BaseModel, Field

from app.schemas.incident import IncidentSignalContext


class RiskLevel(StrEnum):
    """Contextual model categories, not objective claims about a place."""

    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"


class AssessmentConfidence(StrEnum):
    """Confidence in the available signal coverage, not harm probability."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyFactor(BaseModel):
    name: str
    contribution: int = Field(ge=0)
    description: str


class SafetyAssessment(BaseModel):
    """Explainable contextual risk estimate for one requested area."""

    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    confidence: AssessmentConfidence
    factors: list[SafetyFactor]
    incident_count: int = Field(ge=0)
    as_of: datetime
    disclaimer: str


@dataclass(frozen=True)
class SafetyScoringConfig:
    """Centralized scoring constants; weights sum to the 0–100 score range."""

    density_weight: int = 35
    recency_weight: int = 25
    severity_weight: int = 25
    confidence_weight: int = 10
    category_weight: int = 5
    density_cap_per_sq_km: float = 10.0
    category_diversity_cap: int = 3
    recent_window_days: int = 30

    def __post_init__(self) -> None:
        weights = (
            self.density_weight,
            self.recency_weight,
            self.severity_weight,
            self.confidence_weight,
            self.category_weight,
        )
        if any(weight < 0 for weight in weights) or sum(weights) != 100:
            raise ValueError("safety scoring weights must be non-negative and sum to 100")


DEFAULT_SCORING_CONFIG = SafetyScoringConfig()
SAFETY_DISCLAIMER = (
    "This estimate is based on available incident data and is not a guarantee of safety."
)

_SEVERITY_WEIGHTS = {
    "low": 0.20,
    "medium": 0.60,
    "high": 1.00,
}
_CONFIDENCE_WEIGHTS = {
    "unverified": 0.25,
    "corroborated": 0.65,
    "higher_confidence": 0.90,
}


def risk_level_for_score(score: int) -> RiskLevel:
    if score < 25:
        return RiskLevel.LOW
    if score < 50:
        return RiskLevel.MODERATE
    if score < 75:
        return RiskLevel.ELEVATED
    return RiskLevel.HIGH


def _non_negative_count(value: int | None) -> int:
    return max(value or 0, 0)


class SafetyEngine:
    """Pure deterministic incident-derived safety assessment service."""

    def __init__(self, config: SafetyScoringConfig = DEFAULT_SCORING_CONFIG):
        self.config = config

    def assess(self, context: IncidentSignalContext) -> SafetyAssessment:
        incident_count = _non_negative_count(context.incident_count)
        radius_km = max(context.radius_meters / 1000, 0.001)
        area_sq_km = max(pi * radius_km * radius_km, 0.01)
        density_per_sq_km = incident_count / area_sq_km

        density_ratio = min(density_per_sq_km / self.config.density_cap_per_sq_km, 1.0)
        density_contribution = density_ratio * self.config.density_weight

        recent_count = min(_non_negative_count(context.recent_incident_count), incident_count)
        recent_ratio = recent_count / incident_count if incident_count else 0.0
        recency_contribution = recent_ratio * self.config.recency_weight

        severity_total = sum(_non_negative_count(value) for value in context.severity_counts.values())
        severity_signal = (
            sum(
                _non_negative_count(context.severity_counts.get(severity)) * weight
                for severity, weight in _SEVERITY_WEIGHTS.items()
            )
            / severity_total
            if severity_total
            else 0.0
        )
        severity_contribution = severity_signal * self.config.severity_weight

        confidence_total = sum(
            _non_negative_count(value) for value in context.confidence_level_counts.values()
        )
        confidence_signal = (
            sum(
                _non_negative_count(context.confidence_level_counts.get(level)) * weight
                for level, weight in _CONFIDENCE_WEIGHTS.items()
            )
            / confidence_total
            if confidence_total
            else 0.0
        )
        confidence_contribution = confidence_signal * self.config.confidence_weight

        category_count = sum(
            1
            for category, count in context.category_counts.items()
            if category and _non_negative_count(count) > 0
        )
        category_ratio = min(category_count / self.config.category_diversity_cap, 1.0)
        category_contribution = category_ratio * self.config.category_weight

        raw_score = (
            density_contribution
            + recency_contribution
            + severity_contribution
            + confidence_contribution
            + category_contribution
        )
        risk_score = min(max(round(raw_score), 0), 100)
        factor_contributions = [
            round(density_contribution),
            round(recency_contribution),
            round(severity_contribution),
            round(confidence_contribution),
            round(category_contribution),
        ]
        rounding_delta = risk_score - sum(factor_contributions)
        factor_contributions[-1] += rounding_delta
        if factor_contributions[-1] < 0:
            deficit = -factor_contributions[-1]
            factor_contributions[-1] = 0
            for index in sorted(range(4), key=factor_contributions.__getitem__, reverse=True):
                reduction = min(deficit, factor_contributions[index])
                factor_contributions[index] -= reduction
                deficit -= reduction
                if deficit == 0:
                    break

        factors = [
            SafetyFactor(
                name="incident_density",
                contribution=factor_contributions[0],
                description=(
                    f"{incident_count} incident-derived indicators across approximately "
                    f"{area_sq_km:.2f} square kilometres contributed to the estimate."
                ),
            ),
            SafetyFactor(
                name="recent_incident_activity",
                contribution=factor_contributions[1],
                description=(
                    f"{recent_count} of {incident_count} incidents fall within the "
                    f"{self.config.recent_window_days}-day recency window."
                ),
            ),
            SafetyFactor(
                name="severity_activity",
                contribution=factor_contributions[2],
                description="The available severity mix contributed to the estimate.",
            ),
            SafetyFactor(
                name="confidence_adjustment",
                contribution=factor_contributions[3],
                description=(
                    "Available report confidence influenced the estimate; it is not a "
                    "statistical probability."
                ),
            ),
            SafetyFactor(
                name="category_activity",
                contribution=factor_contributions[4],
                description=(
                    f"Indicators span {category_count} reported incident categories in "
                    "the requested context."
                ),
            ),
        ]
        return SafetyAssessment(
            risk_score=risk_score,
            risk_level=risk_level_for_score(risk_score),
            confidence=self._assessment_confidence(context),
            factors=factors,
            incident_count=incident_count,
            as_of=context.as_of,
            disclaimer=SAFETY_DISCLAIMER,
        )

    def _assessment_confidence(self, context: IncidentSignalContext) -> AssessmentConfidence:
        corroborated = _non_negative_count(context.confidence_level_counts.get("corroborated"))
        higher_confidence = _non_negative_count(
            context.confidence_level_counts.get("higher_confidence")
        )
        supported_count = corroborated + higher_confidence
        if supported_count >= 3 or higher_confidence >= 2:
            return AssessmentConfidence.HIGH
        if supported_count >= 1:
            return AssessmentConfidence.MEDIUM
        return AssessmentConfidence.LOW
