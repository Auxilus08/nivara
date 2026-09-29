from datetime import datetime, timezone
from uuid import UUID

import httpx
import pytest

from app.api.dependencies import get_incident_repository
from app.api.routes.routes import get_routing_service
from app.main import app
from app.models.incident import Incident
from app.providers.routing import ProviderRoute
from app.repositories.incident import IncidentRepository
from app.schemas.routes import Coordinate, RouteGeometry, RouteMode, RouteRequest
from app.services.incidents import IncidentService
from app.services.routes import RoutingService


ORIGIN = Coordinate(latitude=12.9716, longitude=77.5946)
DESTINATION = Coordinate(latitude=12.9352, longitude=77.6245)
REPORT_TIME = "2026-09-28T12:00:00Z"


class PersistedIncidentFixtureRepository:
    """Request-independent fixture for report-to-route integration tests.

    The production IncidentRepository performs the corridor filtering with
    PostGIS. This fixture models those bounded results so the API/service flow
    can be tested without pretending that a live database is available.
    """

    def __init__(self):
        self.incidents: list[Incident] = []
        self.route_queries: list[dict] = []

    async def create(self, incident: Incident) -> Incident:
        now = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)
        incident.reported_at = now
        incident.created_at = now
        incident.updated_at = now
        self.incidents.append(incident)
        return incident

    async def get_by_id(self, incident_id: UUID) -> Incident | None:
        return next((item for item in self.incidents if item.id == incident_id), None)

    async def list(self, **filters) -> list[Incident]:
        return self.incidents[: filters.get("limit", 50)]

    async def list_near_route(self, **filters) -> list[Incident]:
        self.route_queries.append(filters)
        middle = filters["coordinates"][1]
        if middle.latitude > 12.98:
            target = (13.0, 77.60)
        else:
            target = (12.94, 77.61)
        return [
            incident
            for incident in self.incidents
            if (incident.latitude, incident.longitude) == target
        ][: filters["limit"]]


class CommunityReportRoutingProvider:
    name = "community-report-provider"

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        return [
            ProviderRoute(
                provider_route_id="fast-report-corridor",
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
                provider_route_id="slow-unaffected-corridor",
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


def route_service(repository: PersistedIncidentFixtureRepository) -> RoutingService:
    return RoutingService(
        CommunityReportRoutingProvider(),
        context_provider=IncidentService(repository),
        corridor_radius_meters=100,
    )


@pytest.mark.asyncio
async def test_community_report_persists_and_changes_subsequent_route_assessments():
    repository = PersistedIncidentFixtureRepository()
    service = route_service(repository)

    async def override_repository():
        return repository

    async def override_routing_service():
        return service

    app.dependency_overrides[get_incident_repository] = override_repository
    app.dependency_overrides[get_routing_service] = override_routing_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            baseline = await client.post(
                "/api/v1/routes",
                json={
                    "origin": ORIGIN.model_dump(),
                    "destination": DESTINATION.model_dump(),
                    "mode": "safety_priority",
                },
            )
            report = await client.post(
                "/api/v1/incidents/reports",
                json={
                    "category": "harassment",
                    "description": "A reported incident occurred beside this route.",
                    "latitude": 13.0,
                    "longitude": 77.60,
                    "occurred_at": REPORT_TIME,
                    "severity": "high",
                },
            )
            outside_report = await client.post(
                "/api/v1/incidents/reports",
                json={
                    "category": "theft",
                    "description": "A report outside the candidate route corridors.",
                    "latitude": 12.80,
                    "longitude": 77.80,
                    "occurred_at": REPORT_TIME,
                    "severity": "high",
                },
            )
            retrieved = await client.get(f"/api/v1/incidents/{report.json()['id']}")
            after_by_mode = {}
            for mode in ("fastest", "balanced", "safety_priority"):
                after_by_mode[mode] = await client.post(
                    "/api/v1/routes",
                    json={
                        "origin": ORIGIN.model_dump(),
                        "destination": DESTINATION.model_dump(),
                        "mode": mode,
                    },
                )
    finally:
        app.dependency_overrides.clear()

    assert baseline.status_code == 200
    assert baseline.json()["selected_route_id"] == "community-report-provider:fast-report-corridor"
    assert report.status_code == 201
    assert report.json()["status"] == "unverified"
    assert report.json()["confidence"]["level"] == "unverified"
    assert outside_report.status_code == 201
    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == report.json()["id"]
    assert retrieved.json()["source"] == "community_report"

    fastest = after_by_mode["fastest"]
    balanced = after_by_mode["balanced"]
    safety_priority = after_by_mode["safety_priority"]
    assert all(response.status_code == 200 for response in after_by_mode.values())
    assert fastest.json()["selected_route_id"] == "community-report-provider:fast-report-corridor"
    assert balanced.json()["selected_route_id"] == "community-report-provider:slow-unaffected-corridor"
    assert safety_priority.json()["selected_route_id"] == "community-report-provider:slow-unaffected-corridor"

    for response in after_by_mode.values():
        body = response.json()
        assert "not a guarantee of safety" in body["comparison_explanation"]
        report_route = next(
            route for route in body["routes"] if route["route_id"].endswith("fast-report-corridor")
        )
        unaffected_route = next(
            route for route in body["routes"] if route["route_id"].endswith("slow-unaffected-corridor")
        )
        assert report_route["safety_assessment"]["incident_count"] == 1
        assert unaffected_route["safety_assessment"]["incident_count"] == 0
        assert report_route["safety_assessment"]["risk_score"] > unaffected_route["safety_assessment"]["risk_score"]
        assert "description" not in report_route
        assert "source" not in report_route
        assert "reporter" not in report_route

    assert len(repository.route_queries) == 8
    assert all(query["corridor_radius_meters"] == 100 for query in repository.route_queries)


@pytest.mark.asyncio
async def test_incident_repository_commits_new_reports_for_later_requests():
    class TransactionRecordingSession:
        def __init__(self):
            self.added = None
            self.committed = False

        def add(self, incident):
            self.added = incident

        async def flush(self):
            return None

        async def commit(self):
            self.committed = True

        async def refresh(self, incident):
            return None

    session = TransactionRecordingSession()
    incident = Incident(
        category="harassment",
        description="A persisted incident fixture.",
        latitude=13.0,
        longitude=77.60,
        occurred_at=datetime(2026, 9, 28, tzinfo=timezone.utc),
        severity="high",
        source="community_report",
        confidence_level="unverified",
        corroboration_count=0,
        status="unverified",
        confidence_factors=["test"],
    )

    created = await IncidentRepository(session).create(incident)

    assert created is incident
    assert session.added is incident
    assert session.committed
