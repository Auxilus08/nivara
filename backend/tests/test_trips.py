from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from app.api.dependencies import get_safe_trip_location_repository, get_safe_trip_repository
from app.api.dependencies import get_safe_trip_check_in_repository
from app.main import app
from app.models.trip import SafeTrip, SafeTripCheckIn, SafeTripLocation, SafeTripStatus
from app.services.trips import SafeTripDeviationService


class FakeSafeTripRepository:
    def __init__(self):
        self.trips: list[SafeTrip] = []

    async def create(self, trip: SafeTrip) -> SafeTrip:
        now = datetime.now(timezone.utc)
        trip.created_at = now
        self.trips.append(trip)
        return trip

    async def get_by_id(self, trip_id):
        return next((trip for trip in self.trips if trip.id == trip_id), None)

    async def list_history(self):
        return sorted(self.trips, key=lambda trip: (trip.created_at, trip.id), reverse=True)

    async def update(self, trip: SafeTrip) -> SafeTrip:
        return trip


class FakeSafeTripLocationRepository:
    def __init__(self):
        self.locations: list[SafeTripLocation] = []
        self.distance_value = 100.0
        self.received_coordinates = None

    async def create(self, location: SafeTripLocation) -> SafeTripLocation:
        if location.received_at is None:
            location.received_at = datetime.now(timezone.utc)
        self.locations.append(location)
        return location

    async def get_latest_for_trip(self, trip_id):
        matching = [location for location in self.locations if location.trip_id == trip_id]
        return max(matching, key=lambda location: (location.recorded_at, location.received_at), default=None)

    async def distance_from_route_meters(self, location, coordinates):
        self.received_coordinates = coordinates
        return self.distance_value


class FakeSafeTripCheckInRepository:
    def __init__(self):
        self.check_ins: list[SafeTripCheckIn] = []

    async def create(self, check_in: SafeTripCheckIn) -> SafeTripCheckIn:
        self.check_ins.append(check_in)
        return check_in


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


def stored_trip(status: str = SafeTripStatus.PLANNED.value, started_at: datetime | None = None) -> SafeTrip:
    now = datetime.now(timezone.utc)
    return SafeTrip(
        id=uuid4(),
        selected_route_id="provider:route-1",
        origin_latitude=12.9716,
        origin_longitude=77.5946,
        destination_latitude=12.9352,
        destination_longitude=77.6245,
        route_distance_meters=4200,
        route_duration_seconds=900,
        route_geometry=[
            {"latitude": 12.9716, "longitude": 77.5946},
            {"latitude": 12.9352, "longitude": 77.6245},
        ],
        expected_arrival_at=now + timedelta(hours=1),
        status=status,
        started_at=started_at,
        created_at=now,
    )


def location_payload(recorded_at: str):
    return {"latitude": 12.968, "longitude": 77.598, "recorded_at": recorded_at}


def stored_location(trip_id, recorded_at: datetime, latitude: float = 12.968) -> SafeTripLocation:
    return SafeTripLocation(
        id=uuid4(),
        trip_id=trip_id,
        latitude=latitude,
        longitude=77.598,
        location=None,
        recorded_at=recorded_at,
        received_at=recorded_at + timedelta(seconds=1),
    )


def location_overrides(trip_repository, location_repository):
    async def override_trip_repository():
        return trip_repository

    async def override_location_repository():
        return location_repository

    app.dependency_overrides[get_safe_trip_repository] = override_trip_repository
    app.dependency_overrides[get_safe_trip_location_repository] = override_location_repository


def history_overrides(repository):
    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository


def check_in_overrides(trip_repository, check_in_repository):
    async def override_trip_repository():
        return trip_repository

    async def override_check_in_repository():
        return check_in_repository

    app.dependency_overrides[get_safe_trip_repository] = override_trip_repository
    app.dependency_overrides[get_safe_trip_check_in_repository] = override_check_in_repository


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
async def test_safe_trip_history_empty_response_is_successful():
    repository = FakeSafeTripRepository()
    history_overrides(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/trips/history")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"trips": [], "count": 0}


@pytest.mark.asyncio
async def test_safe_trip_history_returns_lifecycle_fields_without_sensitive_records():
    repository = FakeSafeTripRepository()
    created = stored_trip(status=SafeTripStatus.PLANNED.value)
    active = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    completed = stored_trip(status=SafeTripStatus.COMPLETED.value, started_at=datetime.now(timezone.utc))
    completed.completed_at = datetime.now(timezone.utc)
    created.created_at = datetime.now(timezone.utc) - timedelta(minutes=3)
    active.created_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    completed.created_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    repository.trips.extend([created, active, completed])
    history_overrides(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/trips/history")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3
    assert [item["id"] for item in body["trips"]] == [str(completed.id), str(active.id), str(created.id)]
    assert [item["status"] for item in body["trips"]] == ["completed", "active", "planned"]
    assert body["trips"][0]["started_at"] is not None
    assert body["trips"][0]["completed_at"] is not None
    assert body["trips"][2]["started_at"] is None
    assert body["trips"][2]["completed_at"] is None
    assert set(body["trips"][0]) == {
        "id", "status", "created_at", "started_at", "completed_at",
        "expected_arrival_at", "origin", "destination",
    }
    assert "geometry" not in body["trips"][0]
    assert "locations" not in body["trips"][0]
    assert "check_ins" not in body["trips"][0]
    assert "deviation" not in body["trips"][0]


@pytest.mark.asyncio
async def test_safe_trip_history_uses_trip_id_as_deterministic_tie_breaker():
    repository = FakeSafeTripRepository()
    timestamp = datetime.now(timezone.utc)
    first = stored_trip()
    second = stored_trip()
    first.created_at = timestamp
    second.created_at = timestamp
    repository.trips.extend([first, second])
    history_overrides(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/trips/history")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    expected = sorted([str(first.id), str(second.id)], reverse=True)
    assert [item["id"] for item in response.json()["trips"]] == expected


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


@pytest.mark.asyncio
async def test_safe_trip_start_activates_plan_and_preserves_snapshot():
    repository = FakeSafeTripRepository()
    trip = stored_trip()
    repository.trips.append(trip)
    original_snapshot = (trip.selected_route_id, trip.route_geometry.copy(), trip.expected_arrival_at)
    before = datetime.now(timezone.utc)

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/start")
    finally:
        app.dependency_overrides.clear()

    after = datetime.now(timezone.utc)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(trip.id)
    assert body["status"] == "active"
    assert body["started_at"] is not None
    started_at = datetime.fromisoformat(body["started_at"])
    assert started_at.tzinfo is not None
    assert before <= started_at <= after
    assert (body["selected_route_id"], body["geometry"], datetime.fromisoformat(body["expected_arrival_at"])) == (
        original_snapshot[0],
        {"coordinates": original_snapshot[1]},
        original_snapshot[2],
    )
    assert repository.trips[0].status == SafeTripStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_safe_trip_start_returns_not_found_for_unknown_trip():
    repository = FakeSafeTripRepository()

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{uuid4()}/start")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Safe Trip not found"


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [SafeTripStatus.ACTIVE.value, SafeTripStatus.COMPLETED.value])
async def test_safe_trip_start_rejects_illegal_lifecycle_state(state: str):
    repository = FakeSafeTripRepository()
    trip = stored_trip(status=state, started_at=datetime.now(timezone.utc) if state == "active" else None)
    repository.trips.append(trip)

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/start")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "cannot be started" in response.json()["detail"]
    assert trip.status == state


@pytest.mark.asyncio
async def test_safe_trip_duplicate_start_is_rejected():
    repository = FakeSafeTripRepository()
    trip = stored_trip()
    repository.trips.append(trip)

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(f"/api/v1/trips/{trip.id}/start")
            second = await client.post(f"/api/v1/trips/{trip.id}/start")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_active_trip_completion_is_server_timestamped_and_updates_lifecycle():
    repository = FakeSafeTripRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    repository.trips.append(trip)

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        before = datetime.now(timezone.utc)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/complete")
        after = datetime.now(timezone.utc)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(trip.id)
    assert body["status"] == "completed"
    completed_at = datetime.fromisoformat(body["completed_at"])
    assert completed_at.tzinfo is not None
    assert before <= completed_at <= after
    assert trip.status == SafeTripStatus.COMPLETED.value
    assert trip.completed_at == completed_at
    assert set(body) == {
        "id", "selected_route_id", "origin", "destination", "distance_meters",
        "estimated_duration_seconds", "geometry", "expected_arrival_at", "status",
        "started_at", "completed_at", "created_at",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [SafeTripStatus.PLANNED.value, SafeTripStatus.COMPLETED.value])
async def test_safe_trip_completion_rejects_invalid_lifecycle_state(state: str):
    repository = FakeSafeTripRepository()
    original_completed_at = datetime.now(timezone.utc) if state == SafeTripStatus.COMPLETED.value else None
    trip = stored_trip(status=state, started_at=datetime.now(timezone.utc) if state == "active" else None)
    trip.completed_at = original_completed_at
    repository.trips.append(trip)

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/complete")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert trip.status == state
    assert trip.completed_at == original_completed_at


@pytest.mark.asyncio
async def test_safe_trip_completion_returns_not_found_for_unknown_trip():
    repository = FakeSafeTripRepository()

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{uuid4()}/complete")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_safe_trip_duplicate_completion_preserves_original_timestamp():
    repository = FakeSafeTripRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    repository.trips.append(trip)

    async def override_repository():
        return repository

    app.dependency_overrides[get_safe_trip_repository] = override_repository
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(f"/api/v1/trips/{trip.id}/complete")
            original_completed_at = trip.completed_at
            second = await client.post(f"/api/v1/trips/{trip.id}/complete")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 409
    assert trip.completed_at == original_completed_at


def test_completion_migration_adds_only_nullable_timezone_aware_timestamp():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0006_add_safe_trip_completion.py"
    source = migration.read_text()

    assert 'revision: str = "0006_add_safe_trip_completion"' in source
    assert 'down_revision: Union[str, None] = "0005_create_safe_trip_check_ins"' in source
    assert 'op.add_column("safe_trips", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))' in source
    assert 'op.drop_column("safe_trips", "completed_at")' in source
    assert "safe_trip_locations" not in source
    assert "op.create_table(\"safe_trip_check_ins\"" not in source


@pytest.mark.asyncio
async def test_active_trip_check_in_is_server_timestamped_and_minimal():
    trip_repository = FakeSafeTripRepository()
    check_in_repository = FakeSafeTripCheckInRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    trip_repository.trips.append(trip)
    check_in_overrides(trip_repository, check_in_repository)
    try:
        before = datetime.now(timezone.utc)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/check-ins")
        after = datetime.now(timezone.utc)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["trip_id"] == str(trip.id)
    checked_in_at = datetime.fromisoformat(body["checked_in_at"])
    assert checked_in_at.tzinfo is not None
    assert before <= checked_in_at <= after
    assert set(body) == {"id", "trip_id", "checked_in_at"}
    assert len(check_in_repository.check_ins) == 1
    assert check_in_repository.check_ins[0].trip_id == trip.id


@pytest.mark.asyncio
async def test_active_trip_allows_repeated_check_ins_as_separate_records():
    trip_repository = FakeSafeTripRepository()
    check_in_repository = FakeSafeTripCheckInRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    trip_repository.trips.append(trip)
    check_in_overrides(trip_repository, check_in_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(f"/api/v1/trips/{trip.id}/check-ins")
            second = await client.post(f"/api/v1/trips/{trip.id}/check-ins")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert len(check_in_repository.check_ins) == 2
    assert check_in_repository.check_ins[0].checked_in_at.tzinfo is not None
    assert check_in_repository.check_ins[1].checked_in_at.tzinfo is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [SafeTripStatus.PLANNED.value, SafeTripStatus.COMPLETED.value])
async def test_inactive_trip_check_in_returns_conflict_without_persistence(state: str):
    trip_repository = FakeSafeTripRepository()
    check_in_repository = FakeSafeTripCheckInRepository()
    trip_repository.trips.append(stored_trip(status=state))
    check_in_overrides(trip_repository, check_in_repository)
    try:
        trip = trip_repository.trips[0]
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/check-ins")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert check_in_repository.check_ins == []


@pytest.mark.asyncio
async def test_check_in_returns_not_found_for_unknown_trip():
    trip_repository = FakeSafeTripRepository()
    check_in_repository = FakeSafeTripCheckInRepository()
    check_in_overrides(trip_repository, check_in_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{uuid4()}/check-ins")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert check_in_repository.check_ins == []


def test_check_in_migration_uses_dedicated_minimal_table():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0005_create_safe_trip_check_ins.py"
    source = migration.read_text()

    assert '"safe_trip_check_ins"' in source
    assert 'sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False)' in source
    assert '"checked_in_at"' in source
    assert 'ForeignKeyConstraint(["trip_id"], ["safe_trips.id"], ondelete="CASCADE")' in source
    assert '"ix_safe_trip_check_ins_trip_id"' in source
    assert '"ix_safe_trip_check_ins_checked_in_at"' in source
    assert "route_geometry" not in source
    assert "latitude" not in source


@pytest.mark.asyncio
async def test_active_trip_location_update_succeeds_and_returns_only_persisted_location():
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    trip_repository.trips.append(trip)
    recorded_at = (datetime.now(timezone.utc) - timedelta(seconds=3)).isoformat()
    location_overrides(trip_repository, location_repository)
    try:
        before = datetime.now(timezone.utc)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/locations", json=location_payload(recorded_at))
        after = datetime.now(timezone.utc)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["trip_id"] == str(trip.id)
    assert body["latitude"] == 12.968
    assert body["longitude"] == 77.598
    assert datetime.fromisoformat(body["recorded_at"]).tzinfo is not None
    received_at = datetime.fromisoformat(body["received_at"])
    assert before <= received_at <= after
    assert set(body) == {"id", "trip_id", "latitude", "longitude", "recorded_at", "received_at"}
    assert len(location_repository.locations) == 1
    assert location_repository.locations[0].trip_id == trip.id
    assert trip.status == SafeTripStatus.ACTIVE.value


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [SafeTripStatus.PLANNED.value, SafeTripStatus.COMPLETED.value])
async def test_inactive_trip_location_update_returns_conflict(state: str):
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=state)
    trip_repository.trips.append(trip)
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/trips/{trip.id}/locations",
                json=location_payload(datetime.now(timezone.utc).isoformat()),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert location_repository.locations == []


@pytest.mark.asyncio
async def test_location_update_returns_not_found_for_unknown_trip():
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/trips/{uuid4()}/locations",
                json=location_payload(datetime.now(timezone.utc).isoformat()),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert location_repository.locations == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"latitude": 91, "longitude": 77.598, "recorded_at": "2026-09-29T12:00:00+00:00"},
        {"latitude": 12.968, "longitude": 181, "recorded_at": "2026-09-29T12:00:00+00:00"},
        {"latitude": 12.968, "longitude": 77.598, "recorded_at": "2026-09-29T12:00:00"},
    ],
)
async def test_location_update_rejects_invalid_coordinates_or_naive_timestamp(payload):
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    trip_repository.trips.append(trip)
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/api/v1/trips/{trip.id}/locations", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert location_repository.locations == []


@pytest.mark.asyncio
async def test_active_trip_accepts_multiple_location_updates_without_returning_history():
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    trip_repository.trips.append(trip)
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post(
                f"/api/v1/trips/{trip.id}/locations",
                json=location_payload(datetime.now(timezone.utc).isoformat()),
            )
            second = await client.post(
                f"/api/v1/trips/{trip.id}/locations",
                json={**location_payload(datetime.now(timezone.utc).isoformat()), "latitude": 12.969},
            )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 201
    assert second.status_code == 201
    assert len(location_repository.locations) == 2
    assert "locations" not in second.json()
    assert "route_geometry" not in second.json()


def test_location_migration_uses_dedicated_postgis_table_and_indexes():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0004_create_safe_trip_locations.py"
    source = migration.read_text()

    assert '"safe_trip_locations"' in source
    assert 'ForeignKeyConstraint(["trip_id"], ["safe_trips.id"], ondelete="CASCADE")' in source
    assert 'Geometry(geometry_type="POINT", srid=4326' in source
    assert '"ix_safe_trip_locations_trip_id"' in source
    assert '"ix_safe_trip_locations_recorded_at"' in source
    assert '"ix_safe_trip_locations_location_gist"' in source
    assert '"route_geometry"' not in source


@pytest.mark.asyncio
async def test_active_trip_deviation_uses_latest_location_and_returns_minimal_assessment():
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value, started_at=datetime.now(timezone.utc))
    trip_repository.trips.append(trip)
    older = stored_location(trip.id, datetime.now(timezone.utc) - timedelta(minutes=2), latitude=13.1)
    newer = stored_location(trip.id, datetime.now(timezone.utc) - timedelta(minutes=1))
    location_repository.locations.extend([older, newer])
    location_repository.distance_value = 742.5
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/trips/{trip.id}/deviation")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["trip_id"] == str(trip.id)
    assert body["deviated"] is True
    assert body["distance_from_route_meters"] == 742.5
    assert body["threshold_meters"] == 500.0
    assert body["based_on_location_id"] == str(newer.id)
    assert "outside the configured route corridor" in body["explanation"]
    assert [point.model_dump() for point in location_repository.received_coordinates] == trip.route_geometry
    assert set(body) == {
        "trip_id", "deviated", "distance_from_route_meters", "threshold_meters",
        "based_on_location_id", "evaluated_at", "explanation",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [SafeTripStatus.PLANNED.value, SafeTripStatus.COMPLETED.value])
async def test_deviation_evaluation_rejects_inactive_trip(state: str):
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=state)
    trip_repository.trips.append(trip)
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/trips/{trip.id}/deviation")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "cannot be evaluated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_deviation_evaluation_returns_not_found_for_unknown_trip():
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    location_overrides(trip_repository, location_repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/trips/{uuid4()}/deviation")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_active_trip_without_location_is_explicitly_unavailable():
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip_repository.trips.append(stored_trip(status=SafeTripStatus.ACTIVE.value))
    location_overrides(trip_repository, location_repository)
    try:
        trip = trip_repository.trips[0]
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/trips/{trip.id}/deviation")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert "no recorded location" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.parametrize("distance, expected", [(500.0, False), (500.01, True)])
async def test_deviation_threshold_boundary_is_deterministic(distance: float, expected: bool):
    trip_repository = FakeSafeTripRepository()
    location_repository = FakeSafeTripLocationRepository()
    trip = stored_trip(status=SafeTripStatus.ACTIVE.value)
    trip_repository.trips.append(trip)
    location_repository.locations.append(stored_location(trip.id, datetime.now(timezone.utc)))
    location_repository.distance_value = distance

    assessment = await SafeTripDeviationService(
        trip_repository,
        location_repository,
        threshold_meters=500.0,
    ).evaluate_trip(trip.id)

    assert assessment.deviated is expected


def test_deviation_repository_uses_metric_postgis_distance_and_planned_geometry():
    source = Path(__file__).parents[1].joinpath("app", "repositories", "trip_location.py").read_text()

    assert "ST_Distance" in source
    assert "Geography" in source
    assert "LINESTRING(" in source
    assert "coordinate.longitude" in source
    assert "coordinate.latitude" in source
