from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.main import app
from app.models.emergency import EmergencyStatus
from app.schemas.routes import Coordinate, RouteGeometry
from app.schemas.trip import SafeTripCreate, SafeTripLocationCreate
from app.schemas.trusted_contact import TrustedContactCreate
from app.schemas.emergency import EmergencyCreate
from app.services.emergencies import EmergencyService
from app.services.trusted_contacts import TrustedContactService
from app.services.trips import (
    SafeTripCheckInService,
    SafeTripDeviationService,
    SafeTripLocationService,
    SafeTripService,
    SafeTripTrustedContactService,
)
from app.services.emergency_notifications import MockEmergencyNotificationProvider


class MemoryTripRepository:
    def __init__(self): self.items = []
    async def create(self, item): self.items.append(item); return item
    async def get_by_id(self, item_id): return next((item for item in self.items if item.id == item_id), None)
    async def update(self, item): return item
    async def list_history(self): return list(self.items)


class MemoryLocationRepository:
    def __init__(self): self.items = []
    async def create(self, item): self.items.append(item); return item
    async def get_latest_for_trip(self, trip_id): return self.items[-1] if self.items else None
    async def distance_from_route_meters(self, location, coordinates): return 0.0


class MemoryCheckInRepository:
    def __init__(self): self.items = []
    async def create(self, item): self.items.append(item); return item


class MemoryContactRepository:
    def __init__(self): self.items = []
    async def create(self, item): self.items.append(item); return item
    async def get_active_by_id(self, item_id): return next((item for item in self.items if item.id == item_id and item.is_active), None)


class MemoryAssociationRepository:
    def __init__(self): self.items = []
    async def get(self, trip_id, contact_id): return next((item for item in self.items if item.safe_trip_id == trip_id and item.trusted_contact_id == contact_id), None)
    async def create(self, item): self.items.append(item); return item
    async def list_for_trip(self, trip_id): return []
    async def delete(self, item): self.items.remove(item)


class MemoryEmergencyRepository:
    def __init__(self): self.items = []
    async def create(self, item): self.items.append(item); return item
    async def get_by_id(self, item_id): return next((item for item in self.items if item.id == item_id), None)
    async def get_active_for_trip(self, trip_id): return next((item for item in self.items if item.trip_id == trip_id and item.status in {"active", "acknowledged"}), None)
    async def update(self, item): return item


@pytest.mark.asyncio
async def test_safe_trip_to_emergency_is_deterministic_and_privacy_aware():
    trips, locations = MemoryTripRepository(), MemoryLocationRepository()
    contacts, associations = MemoryContactRepository(), MemoryAssociationRepository()
    checkins, emergencies = MemoryCheckInRepository(), MemoryEmergencyRepository()
    origin = Coordinate(latitude=21.145, longitude=79.089)
    destination = Coordinate(latitude=21.15, longitude=79.095)
    request = SafeTripCreate(
        selected_route_id="demo-route",
        origin=origin,
        destination=destination,
        distance_meters=1000,
        estimated_duration_seconds=600,
        geometry=RouteGeometry(coordinates=[origin, destination]),
        expected_arrival_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    trip = await SafeTripService(trips).create(request)
    started = await SafeTripService(trips).start(trip.id)
    assert started.status == "active"
    location = await SafeTripLocationService(trips, locations).record(
        trip.id,
        SafeTripLocationCreate(latitude=origin.latitude, longitude=origin.longitude, recorded_at=datetime.now(timezone.utc)),
    )
    deviation = await SafeTripDeviationService(trips, locations, 500).evaluate_trip(trip.id)
    assert deviation.deviated is False
    checkin = await SafeTripCheckInService(trips, checkins).record(trip.id)
    assert checkin.trip_id == trip.id and location.trip_id == trip.id

    contact = await TrustedContactService(contacts).create(TrustedContactCreate(name="Demo Contact", contact_method="email", contact_value="demo@example.test"))
    association = await SafeTripTrustedContactService(trips, contacts, associations).attach(trip.id, contact.id)
    assert association.trusted_contact_id == contact.id

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        privacy = await client.patch("/api/v1/privacy/settings", json={"location_sharing_enabled": True, "trusted_contact_sharing_enabled": False, "emergency_sharing_enabled": False})
    assert privacy.status_code == 200

    provider = MockEmergencyNotificationProvider()
    emergency_service = EmergencyService(
        emergencies,
        trips,
        locations,
        provider,
    )
    created = await emergency_service.create(EmergencyCreate(trip_id=trip.id))
    assert created.status == EmergencyStatus.ACTIVE.value
    assert created.latitude == origin.latitude and created.longitude == origin.longitude
    assert created.sharing_status == "sharing_disabled"
    assert provider.notifications[0]["contact_ids"] == []
    acknowledged = await emergency_service.transition(created.id, EmergencyStatus.ACKNOWLEDGED)
    resolved = await emergency_service.transition(created.id, EmergencyStatus.RESOLVED)
    assert acknowledged.acknowledged_at is not None
    assert resolved.status == EmergencyStatus.RESOLVED.value and resolved.resolved_at is not None
