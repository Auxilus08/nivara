from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.incident import IncidentSignalContext
from app.services.safety import (
    AssessmentConfidence,
    DEFAULT_SCORING_CONFIG,
    RiskLevel,
    SafetyEngine,
    risk_level_for_score,
)


AS_OF = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)


def context(**overrides) -> IncidentSignalContext:
    values = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "radius_meters": 500,
        "as_of": AS_OF,
        "incident_count": 0,
        "recent_incident_count": 0,
        "severity_counts": {},
        "category_counts": {},
        "confidence_level_counts": {},
        "indicator_notes": [],
    }
    values.update(overrides)
    return IncidentSignalContext(**values)


def test_empty_context_is_low_and_disclosed_as_limited_data():
    assessment = SafetyEngine().assess(context())

    assert assessment.risk_score == 0
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.confidence == AssessmentConfidence.LOW
    assert "not a guarantee of safety" in assessment.disclaimer
    assert all(factor.contribution == 0 for factor in assessment.factors)


def test_single_low_severity_incident_has_lower_estimated_risk_indicators():
    assessment = SafetyEngine().assess(
        context(
            incident_count=1,
            recent_incident_count=0,
            severity_counts={"low": 1},
            category_counts={"theft": 1},
            confidence_level_counts={"unverified": 1},
        )
    )

    assert 0 < assessment.risk_score < 25
    assert assessment.risk_level == RiskLevel.LOW


def test_multiple_recent_incidents_raise_score_and_explain_factors():
    assessment = SafetyEngine().assess(
        context(
            incident_count=6,
            recent_incident_count=6,
            severity_counts={"medium": 4, "high": 2},
            category_counts={"harassment": 3, "theft": 2, "suspicious_activity": 1},
            confidence_level_counts={"corroborated": 4, "higher_confidence": 2},
        )
    )

    assert assessment.risk_score >= 75
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.confidence == AssessmentConfidence.HIGH
    assert {factor.name for factor in assessment.factors} == {
        "incident_density",
        "recent_incident_activity",
        "severity_activity",
        "confidence_adjustment",
        "category_activity",
    }
    assert sum(factor.contribution for factor in assessment.factors) == assessment.risk_score


def test_recent_incidents_contribute_more_than_older_incidents():
    older = context(
        incident_count=3,
        recent_incident_count=0,
        severity_counts={"medium": 3},
        category_counts={"theft": 3},
        confidence_level_counts={"unverified": 3},
    )
    recent = older.model_copy(update={"recent_incident_count": 3})

    assert SafetyEngine().assess(recent).risk_score > SafetyEngine().assess(older).risk_score


def test_higher_severity_increases_score():
    low = context(
        incident_count=3,
        recent_incident_count=3,
        severity_counts={"low": 3},
        category_counts={"theft": 3},
        confidence_level_counts={"unverified": 3},
    )
    high = low.model_copy(update={"severity_counts": {"high": 3}})

    assert SafetyEngine().assess(high).risk_score > SafetyEngine().assess(low).risk_score


def test_higher_confidence_increases_score_and_assessment_confidence():
    unverified = context(
        incident_count=3,
        recent_incident_count=3,
        severity_counts={"medium": 3},
        category_counts={"harassment": 3},
        confidence_level_counts={"unverified": 3},
    )
    corroborated = unverified.model_copy(
        update={"confidence_level_counts": {"corroborated": 3}}
    )

    unverified_result = SafetyEngine().assess(unverified)
    corroborated_result = SafetyEngine().assess(corroborated)
    assert corroborated_result.risk_score > unverified_result.risk_score
    assert corroborated_result.confidence == AssessmentConfidence.HIGH


def test_scoring_is_deterministic():
    input_context = context(
        incident_count=4,
        recent_incident_count=2,
        severity_counts={"low": 1, "high": 3},
        category_counts={"harassment": 2, "other": 2},
        confidence_level_counts={"unverified": 2, "higher_confidence": 2},
    )

    first = SafetyEngine().assess(input_context)
    second = SafetyEngine().assess(input_context)

    assert first == second


def test_score_is_normalized_even_for_large_inputs():
    assessment = SafetyEngine().assess(
        context(
            radius_meters=25,
            incident_count=100000,
            recent_incident_count=100000,
            severity_counts={"high": 100000},
            category_counts={"harassment": 100000},
            confidence_level_counts={"higher_confidence": 100000},
        )
    )

    assert 0 <= assessment.risk_score <= 100
    assert assessment.risk_level == RiskLevel.HIGH


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, RiskLevel.LOW),
        (24, RiskLevel.LOW),
        (25, RiskLevel.MODERATE),
        (49, RiskLevel.MODERATE),
        (50, RiskLevel.ELEVATED),
        (74, RiskLevel.ELEVATED),
        (75, RiskLevel.HIGH),
        (100, RiskLevel.HIGH),
    ],
)
def test_risk_level_boundaries(score, expected):
    assert risk_level_for_score(score) == expected


def test_engine_uses_centralized_default_configuration():
    assert SafetyEngine().config == DEFAULT_SCORING_CONFIG
    assert sum(
        (
            DEFAULT_SCORING_CONFIG.density_weight,
            DEFAULT_SCORING_CONFIG.recency_weight,
            DEFAULT_SCORING_CONFIG.severity_weight,
            DEFAULT_SCORING_CONFIG.confidence_weight,
            DEFAULT_SCORING_CONFIG.category_weight,
        )
    ) == 100
