from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from app.api.routes.routes import get_routing_service
from app.main import app
from app.models.incident import (
    ConfidenceLevel,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.providers.routing import ProviderRoute
from app.schemas.routes import Coordinate, RouteGeometry, RouteMode, RouteRequest
from app.services.incidents import IncidentService
from app.services.routes import RoutingService


ORIGIN = Coordinate(latitude=12.9716, longitude=77.5946)
DESTINATION = Coordinate(latitude=12.9352, longitude=77.6245)
AS_OF = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def build_incident(
    *,
    severity: IncidentSeverity,
    confidence: ConfidenceLevel,
    category: IncidentCategory = IncidentCategory.HARASSMENT,
) -> Incident:
    occurred_at = AS_OF - timedelta(days=1)
    return Incident(
        id=uuid4(),
        category=category,
        description="Controlled incident fixture for integration validation.",
        latitude=12.95,
        longitude=77.60,
        occurred_at=occurred_at,
        reported_at=occurred_at,
        severity=severity,
        source=(
            IncidentSource.VERIFIED_PARTNER
            if confidence == ConfidenceLevel.HIGHER_CONFIDENCE
            else IncidentSource.COMMUNITY_REPORT
        ),
        confidence_level=confidence,
        corroboration_count=3 if confidence == ConfidenceLevel.HIGHER_CONFIDENCE else 0,
        status=(
            IncidentStatus.VALIDATED
            if confidence == ConfidenceLevel.HIGHER_CONFIDENCE
            else IncidentStatus.UNVERIFIED
        ),
        confidence_factors=["controlled integration fixture"],
        created_at=occurred_at,
        updated_at=occurred_at,
    )


class CorridorFixtureRepository:
    """In-process stand-in for bounded corridor query results.

    The production repository owns the PostGIS ST_DWithin query. This fixture
    supplies controlled inside/outside results when live PostGIS is unavailable,
    while recording the geometry and corridor passed by the service.
    """

    def __init__(self, route_incidents: dict[str, list[Incident]], outside: Incident):
        self.route_incidents = route_incidents
        self.outside = outside
        self.calls: list[dict] = []
        self.returned_ids: list[list] = []

    async def list_near_route(self, **filters):
        self.calls.append(filters)
        middle_point = filters["coordinates"][1]
        route_key = "high" if middle_point.latitude > 12.98 else "low"
        incidents = self.route_incidents[route_key][: filters["limit"]]
        self.returned_ids.append([incident.id for incident in incidents])
        return incidents


class DeterministicRoutingProvider:
    name = "integration-provider"

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        return [
            ProviderRoute(
                provider_route_id="fast-high-context",
                distance_meters=3600,
                estimated_duration_seconds=90,
                geometry=RouteGeometry(
                    coordinates=[
                        request.origin,
                        Coordinate(latitude=13.0, longitude=77.60),
                        request.destination,
                    ]
                ),
            ),
            ProviderRoute(
                provider_route_id="slow-low-context",
                distance_meters=4800,
                estimated_duration_seconds=120,
                geometry=RouteGeometry(
                    coordinates=[
                        request.origin,
                        Coordinate(latitude=12.94, longitude=77.61),
                        request.destination,
                    ]
                ),
            ),
        ]


def build_integration_service() -> tuple[RoutingService, CorridorFixtureRepository]:
    high_context = [
        build_incident(
            severity=IncidentSeverity.HIGH,
            confidence=ConfidenceLevel.HIGHER_CONFIDENCE,
        )
        for _ in range(8)
    ]
    low_context = [
        build_incident(
            severity=IncidentSeverity.LOW,
            confidence=ConfidenceLevel.UNVERIFIED,
        )
    ]
    outside = build_incident(
        severity=IncidentSeverity.HIGH,
        confidence=ConfidenceLevel.HIGHER_CONFIDENCE,
        category=IncidentCategory.THEFT,
    )
    repository = CorridorFixtureRepository(
        {"high": high_context, "low": low_context}, outside
    )
    context_provider = IncidentService(repository)
    return (
        RoutingService(
            DeterministicRoutingProvider(),
            context_provider=context_provider,
            corridor_radius_meters=100,
        ),
        repository,
    )


@pytest.mark.asyncio
async def test_route_pipeline_passes_geometry_through_context_and_safety_engine():
    service, repository = build_integration_service()

    response = await service.calculate_routes(
        RouteRequest(origin=ORIGIN, destination=DESTINATION, mode=RouteMode.FASTEST)
    )

    assert len(repository.calls) == 2
    assert all(call["corridor_radius_meters"] == 100 for call in repository.calls)
    assert all(len(call["coordinates"]) == 3 for call in repository.calls)

    high_route, low_route = response.routes
    assert high_route.route_id == "integration-provider:fast-high-context"
    assert low_route.route_id == "integration-provider:slow-low-context"
    assert high_route.safety_assessment is not None
    assert low_route.safety_assessment is not None
    assert high_route.safety_assessment.incident_count == 8
    assert low_route.safety_assessment.incident_count == 1
    assert high_route.safety_assessment.risk_score > low_route.safety_assessment.risk_score
    assert any(factor.name == "incident_density" for factor in high_route.safety_assessment.factors)
    assert "not a guarantee of safety" in high_route.safety_assessment.disclaimer
    assert all(repository.outside.id not in returned for returned in repository.returned_ids)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "expected_route"),
    [
        (RouteMode.FASTEST, "integration-provider:fast-high-context"),
        (RouteMode.BALANCED, "integration-provider:fast-high-context"),
        (RouteMode.SAFETY_PRIORITY, "integration-provider:slow-low-context"),
    ],
)
async def test_route_api_validates_all_modes_through_safety_pipeline(mode, expected_route):
    service, _ = build_integration_service()

    async def override_service():
        return service

    app.dependency_overrides[get_routing_service] = override_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/routes",
                json={
                    "origin": ORIGIN.model_dump(),
                    "destination": DESTINATION.model_dump(),
                    "mode": mode.value,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == mode.value
    assert body["selected_route_id"] == expected_route
    assert "not a guarantee of safety" in body["comparison_explanation"]
    assert len(body["routes"]) == 2
    assert body["selected_route_id"] in {route["route_id"] for route in body["routes"]}
    for route in body["routes"]:
        assert route["geometry"]["coordinates"]
        assert route["safety_assessment"]["incident_count"] in {1, 8}
        assert route["comparison_cost"] is not None
        assert route["normalized_travel_score"] is not None
        assert "description" not in route
        assert "reporter" not in route
        assert "private" not in route


@pytest.mark.asyncio
async def test_missing_context_remains_explicit_and_does_not_become_zero_risk():
    class GeometrylessProvider:
        name = "geometryless-provider"

        async def route(self, request: RouteRequest) -> list[ProviderRoute]:
            return [
                ProviderRoute(
                    provider_route_id="short",
                    distance_meters=1000,
                    estimated_duration_seconds=60,
                ),
                ProviderRoute(
                    provider_route_id="long",
                    distance_meters=2000,
                    estimated_duration_seconds=120,
                ),
            ]

    service, _ = build_integration_service()
    service = RoutingService(
        GeometrylessProvider(),
        context_provider=service.context_provider,
    )

    response = await service.calculate_routes(
        RouteRequest(origin=ORIGIN, destination=DESTINATION, mode=RouteMode.SAFETY_PRIORITY)
    )

    assert response.selected_route_id == "geometryless-provider:short"
    assert all(route.safety_assessment is None for route in response.routes)
    assert all(route.comparison_cost == route.normalized_travel_score for route in response.routes)
    assert "unavailable" in response.comparison_explanation
    assert "only" in response.comparison_explanation
