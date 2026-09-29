from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from app.api.dependencies import (
    get_safe_trip_repository,
    get_safe_trip_trusted_contact_repository,
    get_trusted_contact_repository,
)
from app.main import app
from app.models.trusted_contact import TrustedContact
from app.models.trip import SafeTrip, SafeTripStatus
from app.models.trip_trusted_contact import SafeTripTrustedContact


class FakeTripRepository:
    def __init__(self, trips: list[SafeTrip] | None = None):
        self.trips = trips or []

    async def get_by_id(self, trip_id):
        return next((trip for trip in self.trips if trip.id == trip_id), None)


class FakeContactRepository:
    def __init__(self, contacts: list[TrustedContact] | None = None):
        self.contacts = contacts or []

    async def get_active_by_id(self, contact_id):
        return next(
            (contact for contact in self.contacts if contact.id == contact_id and contact.is_active),
            None,
        )


class FakeAssociationRepository:
    def __init__(self, contacts: list[TrustedContact] | None = None):
        self.contacts = contacts or []
        self.associations: list[SafeTripTrustedContact] = []

    async def get(self, trip_id, contact_id):
        return next(
            (
                association
                for association in self.associations
                if association.safe_trip_id == trip_id and association.trusted_contact_id == contact_id
            ),
            None,
        )

    async def create(self, association):
        self.associations.append(association)
        return association

    async def list_for_trip(self, trip_id):
        contacts_by_id = {contact.id: contact for contact in self.contacts if contact.is_active}
        return [
            (association, contacts_by_id[association.trusted_contact_id])
            for association in self.associations
            if association.safe_trip_id == trip_id and association.trusted_contact_id in contacts_by_id
        ]

    async def delete(self, association):
        self.associations.remove(association)


def stored_trip(status: str = SafeTripStatus.PLANNED.value) -> SafeTrip:
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
        started_at=now if status != SafeTripStatus.PLANNED.value else None,
        created_at=now,
    )


def trusted_contact(name: str = "Asha", active: bool = True) -> TrustedContact:
    now = datetime.now(timezone.utc)
    return TrustedContact(
        id=uuid4(),
        name=name,
        contact_method="email",
        contact_value=f"{name.lower()}@example.com",
        is_active=active,
        created_at=now,
        updated_at=now,
    )


def overrides(trip_repository, contact_repository, association_repository):
    async def trip_override():
        return trip_repository

    async def contact_override():
        return contact_repository

    async def association_override():
        return association_repository

    app.dependency_overrides[get_safe_trip_repository] = trip_override
    app.dependency_overrides[get_trusted_contact_repository] = contact_override
    app.dependency_overrides[get_safe_trip_trusted_contact_repository] = association_override


async def request(method: str, path: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


@pytest.mark.asyncio
async def test_attach_and_list_multiple_contacts_for_planned_trip():
    trip = stored_trip()
    first = trusted_contact()
    second = trusted_contact("Riya")
    trip_repository = FakeTripRepository([trip])
    contact_repository = FakeContactRepository([first, second])
    association_repository = FakeAssociationRepository([first, second])
    overrides(trip_repository, contact_repository, association_repository)
    try:
        attached = await request(
            "POST",
            f"/api/v1/trips/{trip.id}/trusted-contacts",
            json={"trusted_contact_id": str(first.id)},
        )
        attached_second = await request(
            "POST",
            f"/api/v1/trips/{trip.id}/trusted-contacts",
            json={"trusted_contact_id": str(second.id)},
        )
        listed = await request("GET", f"/api/v1/trips/{trip.id}/trusted-contacts")
    finally:
        app.dependency_overrides.clear()

    assert attached.status_code == 201
    assert attached_second.status_code == 201
    assert listed.status_code == 200
    assert listed.json()["count"] == 2
    assert {item["trusted_contact_id"] for item in listed.json()["contacts"]} == {str(first.id), str(second.id)}
    assert set(attached.json()) == {"safe_trip_id", "trusted_contact_id", "created_at", "contact"}
    assert "contact_value" in attached.json()["contact"]


@pytest.mark.asyncio
async def test_empty_association_list_is_successful():
    trip = stored_trip()
    trip_repository = FakeTripRepository([trip])
    contact_repository = FakeContactRepository()
    association_repository = FakeAssociationRepository()
    overrides(trip_repository, contact_repository, association_repository)
    try:
        response = await request("GET", f"/api/v1/trips/{trip.id}/trusted-contacts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"contacts": [], "count": 0}


@pytest.mark.asyncio
async def test_duplicate_unknown_and_inactive_contact_associations_are_rejected():
    trip = stored_trip()
    active = trusted_contact()
    inactive = trusted_contact("Inactive", active=False)
    trip_repository = FakeTripRepository([trip])
    contact_repository = FakeContactRepository([active, inactive])
    association_repository = FakeAssociationRepository([active, inactive])
    overrides(trip_repository, contact_repository, association_repository)
    try:
        first = await request(
            "POST", f"/api/v1/trips/{trip.id}/trusted-contacts", json={"trusted_contact_id": str(active.id)}
        )
        duplicate = await request(
            "POST", f"/api/v1/trips/{trip.id}/trusted-contacts", json={"trusted_contact_id": str(active.id)}
        )
        inactive_response = await request(
            "POST", f"/api/v1/trips/{trip.id}/trusted-contacts", json={"trusted_contact_id": str(inactive.id)}
        )
        unknown_response = await request(
            "POST", f"/api/v1/trips/{trip.id}/trusted-contacts", json={"trusted_contact_id": str(uuid4())}
        )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert inactive_response.status_code == 404
    assert unknown_response.status_code == 404


@pytest.mark.asyncio
async def test_unknown_trip_returns_404_for_list_and_attach():
    contact = trusted_contact()
    trip_repository = FakeTripRepository()
    contact_repository = FakeContactRepository([contact])
    association_repository = FakeAssociationRepository([contact])
    overrides(trip_repository, contact_repository, association_repository)
    missing_trip_id = uuid4()
    try:
        listed = await request("GET", f"/api/v1/trips/{missing_trip_id}/trusted-contacts")
        attached = await request(
            "POST",
            f"/api/v1/trips/{missing_trip_id}/trusted-contacts",
            json={"trusted_contact_id": str(contact.id)},
        )
    finally:
        app.dependency_overrides.clear()

    assert listed.status_code == 404
    assert attached.status_code == 404


@pytest.mark.asyncio
async def test_completed_trip_cannot_attach_or_remove_associations():
    trip = stored_trip(SafeTripStatus.COMPLETED.value)
    contact = trusted_contact()
    trip_repository = FakeTripRepository([trip])
    contact_repository = FakeContactRepository([contact])
    association_repository = FakeAssociationRepository([contact])
    overrides(trip_repository, contact_repository, association_repository)
    try:
        attach = await request(
            "POST", f"/api/v1/trips/{trip.id}/trusted-contacts", json={"trusted_contact_id": str(contact.id)}
        )
        remove = await request("DELETE", f"/api/v1/trips/{trip.id}/trusted-contacts/{contact.id}")
    finally:
        app.dependency_overrides.clear()

    assert attach.status_code == 409
    assert remove.status_code == 409


@pytest.mark.asyncio
async def test_remove_association_preserves_trusted_contact():
    trip = stored_trip(SafeTripStatus.ACTIVE.value)
    contact = trusted_contact()
    trip_repository = FakeTripRepository([trip])
    contact_repository = FakeContactRepository([contact])
    association_repository = FakeAssociationRepository([contact])
    overrides(trip_repository, contact_repository, association_repository)
    try:
        attached = await request(
            "POST", f"/api/v1/trips/{trip.id}/trusted-contacts", json={"trusted_contact_id": str(contact.id)}
        )
        removed = await request("DELETE", f"/api/v1/trips/{trip.id}/trusted-contacts/{contact.id}")
        listed = await request("GET", f"/api/v1/trips/{trip.id}/trusted-contacts")
    finally:
        app.dependency_overrides.clear()

    assert attached.status_code == 201
    assert removed.status_code == 204
    assert listed.json() == {"contacts": [], "count": 0}
    assert await contact_repository.get_active_by_id(contact.id) is contact
    assert not hasattr(trip, "contact_value")


def test_association_migration_has_composite_key_foreign_keys_and_downgrade():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0008_create_safe_trip_trusted_contacts.py"
    source = migration.read_text()

    assert 'revision: str = "0008_create_safe_trip_trusted_contacts"' in source
    assert 'down_revision: Union[str, None] = "0007_create_trusted_contacts"' in source
    assert '"safe_trip_trusted_contacts"' in source
    assert '"safe_trip_id"' in source
    assert '"trusted_contact_id"' in source
    assert '"safe_trips.id"' in source
    assert '"trusted_contacts.id"' in source
    assert "PrimaryKeyConstraint" in source
    assert "create_index" in source
    assert "drop_table" in source
