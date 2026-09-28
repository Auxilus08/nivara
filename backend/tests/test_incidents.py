from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest

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
from app.schemas.incident import IncidentReportCreate
from app.services.incidents import IncidentService, calculate_initial_confidence


def build_incident(**overrides) -> Incident:
    now = datetime.now(timezone.utc)
    values = {
        "id": uuid4(),
        "category": IncidentCategory.HARASSMENT,
        "description": "A report with enough detail for testing.",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "occurred_at": now - timedelta(days=1),
        "reported_at": now,
        "severity": IncidentSeverity.MEDIUM,
        "source": IncidentSource.COMMUNITY_REPORT,
        "confidence_level": ConfidenceLevel.UNVERIFIED,
        "corroboration_count": 0,
        "status": IncidentStatus.UNVERIFIED,
        "confidence_factors": ["single community report", "not yet corroborated"],
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return Incident(**values)


class FakeIncidentRepository:
    def __init__(self, incidents: list[Incident] | None = None):
        self.incidents = incidents or []
        self.last_filters = None

    async def create(self, incident: Incident) -> Incident:
        self.incidents.append(incident)
        now = datetime.now(timezone.utc)
        incident.reported_at = now
        incident.created_at = now
        incident.updated_at = now
        return incident

    async def get_by_id(self, incident_id):
        return next((item for item in self.incidents if item.id == incident_id), None)

    async def list(self, **filters):
        self.last_filters = filters
        return self.incidents[: filters["limit"]]


@pytest.fixture
def fake_repository():
    repository = FakeIncidentRepository([build_incident()])
    app.dependency_overrides.clear()
    from app.api.dependencies import get_incident_repository

    async def override_repository():
        return repository

    app.dependency_overrides[get_incident_repository] = override_repository
    yield repository
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_valid_community_report_creates_unverified_incident(fake_repository):
    payload = {
        "category": "poor_lighting",
        "description": "The street lighting was not working near the stop.",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "severity": "low",
    }
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/incidents/reports", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["source"] == "community_report"
    assert body["status"] == "unverified"
    assert body["confidence"]["level"] == "unverified"
    assert body["latitude"] == 12.9716


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"category": "not_a_category", "description": "A sufficiently detailed report.", "latitude": 1, "longitude": 2},
        {"category": "theft", "description": "A sufficiently detailed report.", "latitude": 91, "longitude": 2},
        {"category": "theft", "description": "Too short", "latitude": 1, "longitude": 2},
    ],
)
async def test_community_report_rejects_invalid_input(payload, fake_repository):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/incidents/reports", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_incident_retrieval_and_filters(fake_repository):
    incident = fake_repository.incidents[0]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        retrieved = await client.get(f"/api/v1/incidents/{incident.id}")
        listed = await client.get(
            "/api/v1/incidents",
            params={
                "category": "harassment",
                "latitude": "12.9716",
                "longitude": "77.5946",
                "radius_meters": "500",
            },
        )

    assert retrieved.status_code == 200
    assert retrieved.json()["id"] == str(incident.id)
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    assert fake_repository.last_filters["radius_meters"] == 500


def test_confidence_is_explainable_and_not_probability():
    level, factors = calculate_initial_confidence(IncidentSource.COMMUNITY_REPORT)

    assert level == ConfidenceLevel.UNVERIFIED
    assert factors == ["single community report", "not yet corroborated"]


@pytest.mark.asyncio
async def test_contextual_signal_contract_is_database_independent(fake_repository):
    context = await IncidentService(fake_repository).get_contextual_signals(
        latitude=12.9716,
        longitude=77.5946,
        radius_meters=500,
    )

    assert context.incident_count == 1
    assert context.category_counts == {"harassment": 1}
    assert context.confidence_level_counts == {"unverified": 1}
    assert "unverified community reports" in context.indicator_notes[1]


def test_report_schema_requires_timezone_and_rejects_future_timestamp():
    with pytest.raises(ValueError, match="timezone"):
        IncidentReportCreate(
            category=IncidentCategory.THEFT,
            description="A sufficiently detailed report.",
            latitude=1,
            longitude=2,
            occurred_at=datetime.now(),
        )

    with pytest.raises(ValueError, match="future"):
        IncidentReportCreate(
            category=IncidentCategory.THEFT,
            description="A sufficiently detailed report.",
            latitude=1,
            longitude=2,
            occurred_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_repository_spatial_query_uses_postgis_function():
    class FakeSession:
        def __init__(self):
            self.statement = None

        async def execute(self, statement):
            self.statement = statement

            class Result:
                def scalars(self):
                    return self

                def all(self):
                    return []

            return Result()

    session = FakeSession()
    await IncidentRepository(session).list(latitude=1, longitude=2, radius_meters=500, limit=10)
    from sqlalchemy.dialects.postgresql import dialect

    sql = str(session.statement.compile(dialect=dialect()))
    assert "ST_DWithin" in sql
    assert "incidents.location" in sql
