from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.api.dependencies import (
    get_emergency_repository,
    get_safe_trip_location_repository,
    get_safe_trip_repository,
)
from app.main import app
from app.models.emergency import EmergencyStatus
from app.services.emergencies import (
    EmergencyDuplicateError,
    EmergencyInvalidStateError,
    EmergencyNotFoundError,
    EmergencyService,
    demo_emergency_resources,
)
from app.services.emergency_notifications import MockEmergencyNotificationProvider
from app.schemas.emergency import EmergencyCreate


class FakeEmergencyRepository:
    def __init__(self):
        self.items = []

    async def create(self, item):
        self.items.append(item)
        return item

    async def get_by_id(self, emergency_id):
        return next((item for item in self.items if item.id == emergency_id), None)

    async def get_active_for_trip(self, trip_id):
        return next(
            (item for item in self.items if item.trip_id == trip_id and item.status in {"active", "acknowledged"}),
            None,
        )

    async def update(self, item):
        return item


class FakeTripRepository:
    def __init__(self, trip):
        self.trip = trip

    async def get_by_id(self, trip_id):
        return self.trip if self.trip and self.trip.id == trip_id else None


class FakeLocationRepository:
    def __init__(self, location=None):
        self.location = location

    async def get_latest_for_trip(self, trip_id):
        return self.location


def build_service():
    trip_id = uuid4()
    trip = SimpleNamespace(id=trip_id, status="active")
    location = SimpleNamespace(latitude=21.18, longitude=79.06)
    emergency_repository = FakeEmergencyRepository()
    provider = MockEmergencyNotificationProvider()
    service = EmergencyService(
        emergency_repository,
        FakeTripRepository(trip),
        FakeLocationRepository(location),
        provider,
    )
    return service, trip_id, emergency_repository, provider


@pytest.mark.asyncio
async def test_create_emergency_captures_latest_location_and_uses_mock_provider():
    service, trip_id, repository, provider = build_service()

    response = await service.create(EmergencyCreate(trip_id=trip_id))

    assert response.status == "active"
    assert response.trip_id == trip_id
    assert response.latitude == 21.18
    assert response.longitude == 79.06
    assert response.notification_mode == "mock_demo_only"
    assert len(provider.notifications) == 1
    assert provider.notifications[0]["contact_ids"] == []
    assert len(repository.items) == 1


@pytest.mark.asyncio
async def test_duplicate_active_emergency_is_rejected():
    service, trip_id, _, _ = build_service()
    await service.create(EmergencyCreate(trip_id=trip_id))

    with pytest.raises(EmergencyDuplicateError):
        await service.create(EmergencyCreate(trip_id=trip_id))


@pytest.mark.asyncio
async def test_state_machine_acknowledges_then_resolves_and_rejects_repeats():
    service, trip_id, _, _ = build_service()
    created = await service.create(EmergencyCreate(trip_id=trip_id))

    acknowledged = await service.transition(created.id, EmergencyStatus.ACKNOWLEDGED)
    assert acknowledged.status == "acknowledged"
    assert acknowledged.acknowledged_at is not None

    resolved = await service.transition(created.id, EmergencyStatus.RESOLVED)
    assert resolved.status == "resolved"
    assert resolved.resolved_at is not None

    with pytest.raises(EmergencyInvalidStateError):
        await service.transition(created.id, EmergencyStatus.RESOLVED)


@pytest.mark.asyncio
async def test_unknown_emergency_and_invalid_trip_are_rejected():
    service, trip_id, _, _ = build_service()
    with pytest.raises(EmergencyNotFoundError):
        await service.transition(uuid4(), EmergencyStatus.ACKNOWLEDGED)

    service.trip_repository.trip.status = "planned"
    with pytest.raises(EmergencyInvalidStateError):
        await service.create(EmergencyCreate(trip_id=trip_id))


@pytest.mark.asyncio
async def test_resource_endpoint_returns_demo_placeholders_without_private_fields():
    response = demo_emergency_resources()
    assert response.count == 3
    assert all(item.is_demo_resource for item in response.resources)
    assert all("phone" not in item.model_dump() for item in response.resources)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        api_response = await client.get("/api/v1/emergencies/resources")
    assert api_response.status_code == 200
    assert api_response.json()["resources"]
    assert "contact_value" not in api_response.text


@pytest.mark.asyncio
async def test_emergency_api_response_and_duplicate_status():
    service, trip_id, repository, _ = build_service()

    async def emergency_override():
        return repository

    async def trip_override():
        return service.trip_repository

    async def location_override():
        return service.location_repository

    app.dependency_overrides[get_emergency_repository] = emergency_override
    app.dependency_overrides[get_safe_trip_repository] = trip_override
    app.dependency_overrides[get_safe_trip_location_repository] = location_override
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post("/api/v1/emergencies", json={"trip_id": str(trip_id)})
            duplicate = await client.post("/api/v1/emergencies", json={"trip_id": str(trip_id)})
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 201
    assert duplicate.status_code == 409
    body = first.json()
    assert {"id", "trip_id", "status", "created_at", "notification_mode"} <= set(body)
    assert "contact_value" not in body
    assert datetime.fromisoformat(body["created_at"].replace("Z", "+00:00")).tzinfo is not None
