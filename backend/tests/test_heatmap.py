from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

from app.api.dependencies import get_incident_repository
from app.main import app
from app.models.incident import (
    ConfidenceLevel,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.repositories.incident import IncidentRepository
from app.schemas.heatmap import HeatmapQuery
from app.services.incidents import IncidentService
from app.services.safety import DEFAULT_SCORING_CONFIG, SafetyEngine


AS_OF = datetime(2026, 9, 29, 12, tzinfo=timezone.utc)


def build_incident(*, latitude: float, longitude: float, severity=IncidentSeverity.MEDIUM, confidence=ConfidenceLevel.UNVERIFIED) -> Incident:
    return Incident(
        id=uuid4(),
        category=IncidentCategory.HARASSMENT,
        description="A report with enough detail for heatmap testing.",
        latitude=latitude,
        longitude=longitude,
        occurred_at=AS_OF - timedelta(days=1),
        reported_at=AS_OF,
        severity=severity,
        source=IncidentSource.COMMUNITY_REPORT,
        confidence_level=confidence,
        corroboration_count=0,
        status=IncidentStatus.UNVERIFIED,
        confidence_factors=["single community report"],
        created_at=AS_OF,
        updated_at=AS_OF,
    )


class FakeRepository:
    def __init__(self, incidents: list[Incident]):
        self.incidents = incidents
        self.last_bounds = None

    async def list_in_bounds(self, **filters):
        self.last_bounds = filters
        return self.incidents[: filters["limit"]]


def query() -> HeatmapQuery:
    return HeatmapQuery(
        min_latitude=12.90,
        min_longitude=77.55,
        max_latitude=13.00,
        max_longitude=77.65,
        rows=4,
        columns=4,
    )


def test_heatmap_query_requires_ordered_reasonably_bounded_viewport():
    with pytest.raises(ValueError, match="increasing"):
        HeatmapQuery(
            min_latitude=13,
            min_longitude=77.55,
            max_latitude=12.9,
            max_longitude=77.65,
        )
    with pytest.raises(ValueError, match="too large"):
        HeatmapQuery(
            min_latitude=0,
            min_longitude=0,
            max_latitude=3,
            max_longitude=1,
        )
    with pytest.raises(ValueError, match="privacy"):
        HeatmapQuery(
            min_latitude=12.9,
            min_longitude=77.55,
            max_latitude=12.91,
            max_longitude=77.65,
        )


@pytest.mark.asyncio
async def test_heatmap_aggregation_is_deterministic_and_uses_safety_engine():
    repository = FakeRepository(
        [
            build_incident(latitude=12.91, longitude=77.56),
            build_incident(latitude=12.92, longitude=77.57, severity=IncidentSeverity.HIGH),
            build_incident(
                latitude=12.98,
                longitude=77.64,
                confidence=ConfidenceLevel.HIGHER_CONFIDENCE,
            ),
        ]
    )

    class SpySafetyEngine:
        config = DEFAULT_SCORING_CONFIG

        def __init__(self):
            self.contexts = []
            self.engine = SafetyEngine()

        def assess(self, context):
            self.contexts.append(context)
            return self.engine.assess(context)

    safety_engine = SpySafetyEngine()
    service = IncidentService(repository, safety_engine=safety_engine)

    first = await service.get_heatmap(query())
    second = await service.get_heatmap(query())

    assert first == second
    assert first.incident_count == 3
    assert len(first.points) == 2
    assert len(safety_engine.contexts) == 4
    assert all(point.incident_count > 0 for point in first.points)
    assert all(point.risk_score >= 0 for point in first.points)
    assert first.disclaimer.endswith("not a guarantee of safety.")


@pytest.mark.asyncio
async def test_empty_heatmap_returns_no_points_without_fabricated_risk():
    response = await IncidentService(FakeRepository([])).get_heatmap(query())

    assert response.points == []
    assert response.incident_count == 0
    assert "not a guarantee of safety" in response.disclaimer


@pytest.mark.asyncio
async def test_heatmap_api_valid_response_exposes_only_contextual_fields():
    repository = FakeRepository([build_incident(latitude=12.91, longitude=77.56)])

    async def override_repository():
        return repository

    app.dependency_overrides[get_incident_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/safety/heatmap",
                params={
                    "min_latitude": 12.90,
                    "min_longitude": 77.55,
                    "max_latitude": 13.00,
                    "max_longitude": 77.65,
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["points"]
    assert {"latitude", "longitude", "risk_score", "risk_level", "incident_count", "confidence"} <= set(body["points"][0])
    assert "id" not in body["points"][0]
    assert "description" not in body["points"][0]
    assert "reporter" not in body["points"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params",
    [
        {"min_latitude": 91, "min_longitude": 77, "max_latitude": 92, "max_longitude": 78},
        {"min_latitude": 12, "min_longitude": 181, "max_latitude": 13, "max_longitude": 182},
        {"min_latitude": 12.90, "min_longitude": 77.55, "max_latitude": 15.00, "max_longitude": 77.65},
        {"min_latitude": 12.90, "min_longitude": 77.55, "max_latitude": 12.91, "max_longitude": 77.65},
    ],
)
async def test_heatmap_api_rejects_invalid_or_unbounded_bounds(params):
    async def override_repository():
        return FakeRepository([])

    app.dependency_overrides[get_incident_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/safety/heatmap", params=params)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_heatmap_api_requires_all_geographic_bounds():
    async def override_repository():
        return FakeRepository([])

    app.dependency_overrides[get_incident_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/safety/heatmap",
                params={"min_latitude": 12.90, "min_longitude": 77.55},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_heatmap_repository_uses_bounded_postgis_envelope():
    class FakeSession:
        statement = None

        async def execute(self, statement):
            self.statement = statement

            class Result:
                def scalars(self):
                    return self

                def all(self):
                    return []

            return Result()

    session = FakeSession()
    await IncidentRepository(session).list_in_bounds(
        min_latitude=12.9,
        min_longitude=77.5,
        max_latitude=13.0,
        max_longitude=77.6,
        limit=1000,
    )
    from sqlalchemy.dialects.postgresql import dialect

    sql = str(session.statement.compile(dialect=dialect()))
    assert "ST_Intersects" in sql
    assert "ST_MakeEnvelope" in sql
    assert "LIMIT" in sql
