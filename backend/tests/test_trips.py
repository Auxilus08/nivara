from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.api.dependencies import get_safe_trip_repository
from app.main import app
from app.models.trip import SafeTrip


class FakeSafeTripRepository:
    def __init__(self):
        self.trips: list[SafeTrip] = []

    async def create(self, trip: SafeTrip) -> SafeTrip:
        now = datetime.now(timezone.utc)
        trip.created_at = now
        self.trips.append(trip)
        return trip


def trip_payload(expected_arrival_at: str):
    return {
        "selected_route_id": "provider:route-1",
        "origin": {"latitude": 12.9716, "longitude": 77.5946},
        "destination": {"latitude": 12.9352, "longitude": 77.6245},
        "distance_meters": 4200,
        "estimated_duration_seconds": 900,
        "geometry": {
            "coordinates": [
                {"latitude": 12.9716, "longitude": 77.5946},
                {"latitude": 12.9352, "longitude": 77.6245},
            ]
        },
        "expected_arrival_at": expected_arrival_at,
    }


@pytest.mark.asyncio
async def test_safe_trip_creation_persists_selected_route_snapshot():
    repository = FakeSafeTripRepository()

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        expected = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/trips", json=trip_payload(expected))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["selected_route_id"] == "provider:route-1"
    assert body["geometry"]["coordinates"][0]["latitude"] == 12.9716
    assert body["status"] == "planned"
    assert len(repository.trips) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_arrival_at",
    [
        datetime.now(timezone.utc).isoformat(),
        datetime.now().isoformat(),
    ],
)
async def test_safe_trip_requires_future_timezone_aware_arrival(expected_arrival_at: str):
    repository = FakeSafeTripRepository()

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/trips", json=trip_payload(expected_arrival_at))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert repository.trips == []


@pytest.mark.asyncio
async def test_safe_trip_rejects_route_geometry_with_mismatched_endpoint():
    repository = FakeSafeTripRepository()

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        expected = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        payload = trip_payload(expected)
        payload["geometry"]["coordinates"][0] = {"latitude": 12.0, "longitude": 77.0}
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/trips", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert repository.trips == []

