from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from app.api.dependencies import (
    get_safe_trip_trusted_contact_repository,
    get_trusted_contact_repository,
    get_trusted_contact_sharing_preference_repository,
)
from app.main import app
from app.models.trusted_contact import TrustedContact
from app.models.trusted_contact_sharing_preference import TrustedContactSharingPreference
from app.models.trip import SafeTrip, SafeTripStatus
from app.models.trip_trusted_contact import SafeTripTrustedContact


class FakeContactRepository:
    def __init__(self, contacts: list[TrustedContact]):
        self.contacts = contacts

    async def get_active_by_id(self, contact_id):
        return next(
            (contact for contact in self.contacts if contact.id == contact_id and contact.is_active),
            None,
        )

    async def update(self, contact):
        return contact

    async def deactivate(self, contact):
        contact.is_active = False
        return contact


class FakePreferenceRepository:
    def __init__(self, preferences: list[TrustedContactSharingPreference] | None = None):
        self.preferences = preferences or []
        self.created: list[TrustedContactSharingPreference] = []
        self.updated: list[TrustedContactSharingPreference] = []

    async def get_by_contact_id(self, contact_id):
        return next((item for item in self.preferences if item.trusted_contact_id == contact_id), None)

    async def create(self, preference):
        self.preferences.append(preference)
        self.created.append(preference)
        return preference

    async def update(self, preference):
        self.updated.append(preference)
        return preference


class FakeAssociationRepository:
    def __init__(self, associations: list[SafeTripTrustedContact] | None = None):
        self.associations = associations or []


def contact(name="Asha", active=True):
    now = datetime.now(timezone.utc)
    return TrustedContact(
        id=uuid4(),
        name=name,
        contact_method="email",
        contact_value=f"{name.lower()}@example.com",
        is_active=active,
        created_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )


def preference(contact_id, trip=False, location=False, emergency=False):
    now = datetime.now(timezone.utc)
    return TrustedContactSharingPreference(
        id=uuid4(),
        trusted_contact_id=contact_id,
        allow_trip_status=trip,
        allow_location=location,
        allow_emergency=emergency,
        created_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )


def overrides(contact_repository, preference_repository):
    async def contact_override():
        return contact_repository

    async def preference_override():
        return preference_repository

    app.dependency_overrides[get_trusted_contact_repository] = contact_override
    app.dependency_overrides[get_trusted_contact_sharing_preference_repository] = preference_override


async def request(method: str, path: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


@pytest.mark.asyncio
async def test_update_contact_supports_partial_name_update_and_preserves_identity():
    existing = contact()
    repository = FakeContactRepository([existing])
    overrides(repository, FakePreferenceRepository())
    original_id = existing.id
    original_value = existing.contact_value
    original_created_at = existing.created_at
    try:
        response = await request("PATCH", f"/api/v1/trusted-contacts/{existing.id}", json={"name": "Updated Asha"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(original_id)
    assert body["name"] == "Updated Asha"
    assert body["contact_value"] == original_value
    assert datetime.fromisoformat(body["created_at"]) == original_created_at
    assert datetime.fromisoformat(body["updated_at"]) >= original_created_at


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_method, expected_value",
    [
        ({"contact_value": "new@example.com"}, "email", "new@example.com"),
        ({"contact_method": "phone", "contact_value": "+91 98765 43210"}, "phone", "+91 98765 43210"),
    ],
)
async def test_update_contact_supports_value_and_method_value_updates(payload, expected_method, expected_value):
    existing = contact()
    repository = FakeContactRepository([existing])
    overrides(repository, FakePreferenceRepository())
    try:
        response = await request("PATCH", f"/api/v1/trusted-contacts/{existing.id}", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["contact_method"] == expected_method
    assert response.json()["contact_value"] == expected_value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"contact_value": "not-an-email"},
        {"contact_method": "fax"},
        {"contact_method": "phone"},
        {"contact_method": "email", "contact_value": "not-an-email"},
        {"name": ""},
    ],
)
async def test_update_contact_rejects_empty_or_invalid_partial_updates(payload):
    existing = contact()
    repository = FakeContactRepository([existing])
    overrides(repository, FakePreferenceRepository())
    try:
        response = await request("PATCH", f"/api/v1/trusted-contacts/{existing.id}", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert existing.name == "Asha"


@pytest.mark.asyncio
async def test_update_contact_unknown_or_inactive_returns_404():
    inactive = contact(active=False)
    repository = FakeContactRepository([inactive])
    overrides(repository, FakePreferenceRepository())
    try:
        unknown = await request("PATCH", f"/api/v1/trusted-contacts/{uuid4()}", json={"name": "Unknown"})
        inactive_response = await request("PATCH", f"/api/v1/trusted-contacts/{inactive.id}", json={"name": "Inactive"})
    finally:
        app.dependency_overrides.clear()

    assert unknown.status_code == 404
    assert inactive_response.status_code == 404


@pytest.mark.asyncio
async def test_preferences_get_lazily_initializes_restrictive_defaults():
    existing = contact()
    contact_repository = FakeContactRepository([existing])
    preference_repository = FakePreferenceRepository()
    overrides(contact_repository, preference_repository)
    try:
        response = await request("GET", f"/api/v1/trusted-contacts/{existing.id}/sharing-preferences")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["trusted_contact_id"] == str(existing.id)
    assert body["allow_trip_status"] is False
    assert body["allow_location"] is False
    assert body["allow_emergency"] is False
    assert set(body) == {
        "trusted_contact_id", "allow_trip_status", "allow_location", "allow_emergency", "created_at", "updated_at"
    }
    assert len(preference_repository.created) == 1


@pytest.mark.asyncio
async def test_preferences_patch_supports_each_permission_and_partial_updates():
    existing = contact()
    stored = preference(existing.id)
    contact_repository = FakeContactRepository([existing])
    preference_repository = FakePreferenceRepository([stored])
    overrides(contact_repository, preference_repository)
    try:
        trip_status = await request(
            "PATCH", f"/api/v1/trusted-contacts/{existing.id}/sharing-preferences", json={"allow_trip_status": True}
        )
        location = await request(
            "PATCH", f"/api/v1/trusted-contacts/{existing.id}/sharing-preferences", json={"allow_location": True}
        )
        emergency = await request(
            "PATCH", f"/api/v1/trusted-contacts/{existing.id}/sharing-preferences", json={"allow_emergency": True}
        )
        combined = await request(
            "PATCH",
            f"/api/v1/trusted-contacts/{existing.id}/sharing-preferences",
            json={"allow_trip_status": False, "allow_location": False, "allow_emergency": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert trip_status.status_code == location.status_code == emergency.status_code == combined.status_code == 200
    assert combined.json()["allow_trip_status"] is False
    assert combined.json()["allow_location"] is False
    assert combined.json()["allow_emergency"] is True
    assert len(preference_repository.created) == 0
    assert len(preference_repository.updated) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("path_suffix", ["/sharing-preferences"])
async def test_preferences_reject_empty_patch_and_unknown_or_inactive_contact(path_suffix):
    inactive = contact(active=False)
    repository = FakeContactRepository([inactive])
    overrides(repository, FakePreferenceRepository())
    try:
        empty = await request("PATCH", f"/api/v1/trusted-contacts/{inactive.id}{path_suffix}", json={})
        unknown = await request("GET", f"/api/v1/trusted-contacts/{uuid4()}{path_suffix}")
        inactive_response = await request("GET", f"/api/v1/trusted-contacts/{inactive.id}{path_suffix}")
    finally:
        app.dependency_overrides.clear()

    assert empty.status_code == 422
    assert unknown.status_code == 404
    assert inactive_response.status_code == 404


@pytest.mark.asyncio
async def test_contact_update_and_deactivation_preserve_preferences_and_safe_trip_association():
    existing = contact()
    stored_preference = preference(existing.id, trip=True)
    association = SafeTripTrustedContact(safe_trip_id=uuid4(), trusted_contact_id=existing.id)
    contact_repository = FakeContactRepository([existing])
    preference_repository = FakePreferenceRepository([stored_preference])
    overrides(contact_repository, preference_repository)
    try:
        updated = await request("PATCH", f"/api/v1/trusted-contacts/{existing.id}", json={"name": "Renamed"})
        await request("DELETE", f"/api/v1/trusted-contacts/{existing.id}")
    finally:
        app.dependency_overrides.clear()

    assert updated.status_code == 200
    assert association.trusted_contact_id == existing.id
    assert existing.is_active is False
    assert preference_repository.preferences[0].trusted_contact_id == existing.id
    assert preference_repository.preferences[0].allow_trip_status is True


def test_preference_migration_has_restrictive_defaults_one_to_one_fk_and_downgrade():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0009_create_trusted_contact_sharing_preferences.py"
    source = migration.read_text()

    assert 'revision: str = "0009_create_trusted_contact_sharing_preferences"' in source
    assert 'down_revision: Union[str, None] = "0008_create_safe_trip_trusted_contacts"' in source
    assert '"trusted_contact_sharing_preferences"' in source
    assert "allow_trip_status" in source
    assert "allow_location" in source
    assert "allow_emergency" in source
    assert "server_default=sa.false()" in source
    assert "UniqueConstraint" in source
    assert 'ondelete="RESTRICT"' in source
    assert "drop_table" in source
