from datetime import datetime, timezone

import pytest

from app.providers.routing import ProviderRoute
from app.schemas.incident import IncidentSignalContext
from app.schemas.routes import Coordinate, RouteGeometry, RouteMode, RouteRequest
from app.services.routes import RoutingService
from app.services.route_comparison import (
    DEFAULT_MODE_WEIGHTS,
    MODE_DESCRIPTIONS,
    RouteComparisonService,
)
from app.services.safety import SafetyAssessment, SafetyEngine, risk_level_for_score


ORIGIN = Coordinate(latitude=12.9716, longitude=77.5946)
DESTINATION = Coordinate(latitude=12.9352, longitude=77.6245)


def context(score_seed: int = 1) -> IncidentSignalContext:
    return IncidentSignalContext(
        latitude=12.95,
        longitude=77.60,
        radius_meters=1000 if score_seed == 1 else 100,
        as_of=datetime(2026, 9, 29, tzinfo=timezone.utc),
        incident_count=score_seed,
        recent_incident_count=score_seed,
        severity_counts={"high": score_seed},
        category_counts={"harassment": score_seed},
        confidence_level_counts={"higher_confidence": score_seed},
        indicator_notes=["route corridor context"],
    )


def candidate(route_id: str, duration: int, assessment=None):
    from app.schemas.routes import RouteCandidate

    return RouteCandidate(
        route_id=route_id,
        origin=ORIGIN,
        destination=DESTINATION,
        distance_meters=duration * 4,
        estimated_duration_seconds=duration,
        geometry=RouteGeometry(coordinates=[ORIGIN, DESTINATION]),
        provider="test-provider",
        safety_assessment=assessment,
    )


def test_comparison_normalizes_time_and_selects_deterministically():
    service = RouteComparisonService()
    routes = [candidate("slow", 120), candidate("fast", 60)]

    enriched, selected = service.compare(routes, RouteMode.FASTEST)

    assert selected == "fast"
    assert enriched[0].normalized_travel_score == 100
    assert enriched[1].normalized_travel_score == 50
    assert enriched[0].comparison_cost == 100
    assert enriched[1].comparison_cost == 50
    assert service.compare(routes, RouteMode.FASTEST) == (enriched, selected)


def test_fastest_mode_uses_documented_dominant_time_weight():
    weights = DEFAULT_MODE_WEIGHTS[RouteMode.FASTEST]

    assert weights.time == 0.90
    assert weights.safety == 0.10
    assert weights.time > weights.safety
    assert "shorter travel time" in MODE_DESCRIPTIONS[RouteMode.FASTEST]


def test_fastest_prefers_shorter_route_even_when_it_has_higher_risk():
    engine = SafetyEngine()
    shorter_high_risk = candidate("shorter", 60, engine.assess(context(8)))
    longer_lower_risk = candidate("longer", 120, engine.assess(context(1)))

    routes, selected = RouteComparisonService().compare(
        [shorter_high_risk, longer_lower_risk], RouteMode.FASTEST
    )

    assert selected == "shorter"
    assert routes[0].comparison_cost == pytest.approx(
        0.90 * routes[0].normalized_travel_score
        + 0.10 * shorter_high_risk.safety_assessment.risk_score,
        abs=0.01,
    )
    assert routes[1].comparison_cost == pytest.approx(
        0.90 * routes[1].normalized_travel_score
        + 0.10 * longer_lower_risk.safety_assessment.risk_score,
        abs=0.01,
    )


def test_fastest_same_duration_uses_lower_safety_score():
    engine = SafetyEngine()
    higher_risk = candidate("higher-risk", 90, engine.assess(context(8)))
    lower_risk = candidate("lower-risk", 90, engine.assess(context(1)))

    _, selected = RouteComparisonService().compare(
        [higher_risk, lower_risk], RouteMode.FASTEST
    )

    assert selected == "lower-risk"


def test_fastest_identical_candidates_use_stable_route_id_tie_breaker():
    routes, selected = RouteComparisonService().compare(
        [candidate("route-b", 90), candidate("route-a", 90)], RouteMode.FASTEST
    )

    assert selected == "route-a"
    assert routes[0].comparison_cost == routes[1].comparison_cost


def test_fastest_single_candidate_is_selected_and_keeps_assessment():
    assessment = SafetyEngine().assess(context(1))
    routes, selected = RouteComparisonService().compare(
        [candidate("only-route", 90, assessment)], RouteMode.FASTEST
    )

    assert selected == "only-route"
    assert routes[0].safety_assessment == assessment
    assert routes[0].comparison_cost == pytest.approx(
        0.90 * routes[0].normalized_travel_score + 0.10 * assessment.risk_score
    )


def manual_assessment(risk_score: int) -> SafetyAssessment:
    return SafetyAssessment(
        risk_score=risk_score,
        risk_level=risk_level_for_score(risk_score),
        confidence="medium",
        factors=[],
        incident_count=1,
        as_of=datetime(2026, 9, 29, tzinfo=timezone.utc),
        disclaimer="This estimate is based on available incident data and is not a guarantee of safety.",
    )


def test_balanced_uses_exact_documented_weights():
    weights = DEFAULT_MODE_WEIGHTS[RouteMode.BALANCED]

    assert weights.time == 0.55
    assert weights.safety == 0.45
    assert "available safety indicators" in MODE_DESCRIPTIONS[RouteMode.BALANCED]


def test_balanced_can_choose_slower_route_with_substantially_lower_risk():
    faster_high_risk = candidate("faster-high-risk", 90, manual_assessment(100))
    slower_lower_risk = candidate("slower-lower-risk", 100, manual_assessment(60))

    routes, selected = RouteComparisonService().compare(
        [faster_high_risk, slower_lower_risk], RouteMode.BALANCED
    )

    assert selected == "slower-lower-risk"
    assert routes[0].comparison_cost == 94.5
    assert routes[1].comparison_cost == 82.0


def test_balanced_time_penalty_can_outweigh_lower_risk():
    faster_lower_risk = candidate("faster-lower-risk", 60, manual_assessment(20))
    slower_higher_risk = candidate("slower-higher-risk", 120, manual_assessment(100))

    _, selected = RouteComparisonService().compare(
        [faster_lower_risk, slower_higher_risk], RouteMode.BALANCED
    )

    assert selected == "faster-lower-risk"


def test_balanced_equal_duration_prefers_lower_risk():
    higher_risk = candidate("higher-risk", 90, manual_assessment(80))
    lower_risk = candidate("lower-risk", 90, manual_assessment(30))

    _, selected = RouteComparisonService().compare(
        [higher_risk, lower_risk], RouteMode.BALANCED
    )

    assert selected == "lower-risk"


def test_balanced_equal_cost_uses_existing_deterministic_tie_breaking():
    first = candidate("route-b", 91, manual_assessment(100))
    second = candidate("route-a", 100, manual_assessment(89))

    routes, selected = RouteComparisonService().compare(
        [first, second], RouteMode.BALANCED
    )

    assert routes[0].comparison_cost == routes[1].comparison_cost
    assert selected == "route-b"


def test_safety_priority_uses_exact_documented_weights():
    weights = DEFAULT_MODE_WEIGHTS[RouteMode.SAFETY_PRIORITY]

    assert weights.time == 0.25
    assert weights.safety == 0.75
    assert weights.safety > weights.time
    assert "available safety indicators" in MODE_DESCRIPTIONS[RouteMode.SAFETY_PRIORITY]


def test_safety_priority_can_select_slower_route_with_materially_lower_risk():
    faster_high_risk = candidate("faster-high-risk", 90, manual_assessment(100))
    slower_lower_risk = candidate("slower-lower-risk", 100, manual_assessment(20))

    routes, selected = RouteComparisonService().compare(
        [faster_high_risk, slower_lower_risk], RouteMode.SAFETY_PRIORITY
    )

    assert selected == "slower-lower-risk"
    assert routes[0].comparison_cost == 97.5
    assert routes[1].comparison_cost == 40.0


def test_safety_priority_does_not_ignore_a_large_travel_time_penalty():
    faster_lower_risk = candidate("faster-lower-risk", 60, manual_assessment(20))
    slower_higher_risk = candidate("slower-higher-risk", 120, manual_assessment(100))

    _, selected = RouteComparisonService().compare(
        [faster_lower_risk, slower_higher_risk], RouteMode.SAFETY_PRIORITY
    )

    assert selected == "faster-lower-risk"


def test_safety_priority_equal_duration_prefers_lower_risk():
    higher_risk = candidate("higher-risk", 90, manual_assessment(80))
    lower_risk = candidate("lower-risk", 90, manual_assessment(30))

    _, selected = RouteComparisonService().compare(
        [higher_risk, lower_risk], RouteMode.SAFETY_PRIORITY
    )

    assert selected == "lower-risk"


def test_safety_priority_equal_cost_uses_lower_duration_then_route_id():
    shorter = candidate("route-b", 91, manual_assessment(100))
    longer = candidate("route-a", 100, manual_assessment(97))

    routes, selected = RouteComparisonService().compare(
        [shorter, longer], RouteMode.SAFETY_PRIORITY
    )

    assert routes[0].comparison_cost == routes[1].comparison_cost
    assert selected == "route-b"

    same_duration = [
        candidate("route-b", 100, manual_assessment(50)),
        candidate("route-a", 100, manual_assessment(50)),
    ]
    _, selected_by_id = RouteComparisonService().compare(
        same_duration, RouteMode.SAFETY_PRIORITY
    )
    assert selected_by_id == "route-a"


def test_safety_priority_single_candidate_keeps_assessment_attached():
    assessment = manual_assessment(68)

    routes, selected = RouteComparisonService().compare(
        [candidate("only-route", 90, assessment)], RouteMode.SAFETY_PRIORITY
    )

    assert selected == "only-route"
    assert routes[0].safety_assessment == assessment
    assert routes[0].comparison_cost == pytest.approx(0.25 * 100 + 0.75 * 68)


def test_mode_weights_change_selection_using_safety_assessments():
    engine = SafetyEngine()
    fast_high_risk = candidate("fast-high-risk", 60, engine.assess(context(8)))
    slow_lower_risk = candidate("slow-lower-risk", 120, engine.assess(context(1)))

    _, fastest_selected = RouteComparisonService().compare(
        [fast_high_risk, slow_lower_risk], RouteMode.FASTEST
    )
    _, safety_selected = RouteComparisonService().compare(
        [fast_high_risk, slow_lower_risk], RouteMode.SAFETY_PRIORITY
    )

    assert fastest_selected == "fast-high-risk"
    assert safety_selected == "slow-lower-risk"


def test_missing_safety_context_is_not_treated_as_zero_risk():
    routes, selected = RouteComparisonService().compare(
        [candidate("fast", 60), candidate("slow", 120)], RouteMode.SAFETY_PRIORITY
    )

    assert selected == "fast"
    assert all(route.safety_assessment is None for route in routes)
    assert all(route.comparison_explanation and "unavailable" in route.comparison_explanation for route in routes)


class FakeProvider:
    name = "test-provider"

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        return [
            ProviderRoute(
                provider_route_id="fast",
                distance_meters=2000,
                estimated_duration_seconds=60,
                geometry=RouteGeometry(coordinates=[request.origin, request.destination]),
            ),
            ProviderRoute(
                provider_route_id="slow",
                distance_meters=4000,
                estimated_duration_seconds=120,
                geometry=RouteGeometry(coordinates=[request.origin, request.destination]),
            ),
        ]


class FakeContextProvider:
    def __init__(self):
        self.calls = []

    async def get_route_contextual_signals(self, *, geometry, corridor_radius_meters):
        self.calls.append((geometry, corridor_radius_meters))
        return context(8 if len(self.calls) == 1 else 1)


@pytest.mark.asyncio
async def test_routing_service_enriches_candidates_before_comparison():
    context_provider = FakeContextProvider()
    response = await RoutingService(
        FakeProvider(),
        context_provider=context_provider,
        corridor_radius_meters=125,
    ).calculate_routes(
        RouteRequest(origin=ORIGIN, destination=DESTINATION, mode=RouteMode.SAFETY_PRIORITY)
    )

    assert len(context_provider.calls) == 2
    assert all(route.safety_assessment is not None for route in response.routes)
    assert response.selected_route_id == "test-provider:slow"
    assert response.routes[0].comparison_cost is not None
    assert "not a guarantee of safety" in response.comparison_explanation
