from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from app.api.dependencies import get_trusted_contact_repository
from app.main import app
from app.models.trusted_contact import TrustedContact


class FakeTrustedContactRepository:
    def __init__(self):
        self.contacts: list[TrustedContact] = []
        self.deactivated: list[str] = []

    async def create(self, contact: TrustedContact) -> TrustedContact:
        self.contacts.append(contact)
        return contact

    async def list_active(self) -> list[TrustedContact]:
        return sorted(
            [contact for contact in self.contacts if contact.is_active],
            key=lambda contact: (contact.created_at, contact.id),
            reverse=True,
        )[:100]

    async def get_active_by_id(self, contact_id):
        return next(
            (contact for contact in self.contacts if contact.id == contact_id and contact.is_active),
            None,
        )

    async def deactivate(self, contact: TrustedContact) -> TrustedContact:
        contact.is_active = False
        self.deactivated.append(str(contact.id))
        return contact


def repository_override(repository):
    async def override_repository():
        return repository

    app.dependency_overrides[get_trusted_contact_repository] = override_repository


def contact_payload(name="Asha", method="email", value="asha@example.com"):
    return {"name": name, "contact_method": method, "contact_value": value}


@pytest.mark.asyncio
async def test_create_valid_email_contact_returns_minimal_management_response():
    repository = FakeTrustedContactRepository()
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/trusted-contacts", json=contact_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Asha"
    assert body["contact_method"] == "email"
    assert body["contact_value"] == "asha@example.com"
    assert body["is_active"] is True
    assert body["created_at"]
    assert body["updated_at"]
    assert set(body) == {"id", "name", "contact_method", "contact_value", "is_active", "created_at", "updated_at"}
    assert len(repository.contacts) == 1


@pytest.mark.asyncio
async def test_create_valid_phone_contact():
    repository = FakeTrustedContactRepository()
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/trusted-contacts",
                json=contact_payload(name="Riya", method="phone", value="+91 98765 43210"),
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["contact_method"] == "phone"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        contact_payload(name=""),
        contact_payload(name="   "),
        contact_payload(method="fax"),
        contact_payload(value="not-an-email"),
        contact_payload(method="phone", value="abc"),
        contact_payload(method="phone", value="+91 98765 / 43210"),
        contact_payload(value=""),
    ],
)
async def test_trusted_contact_validation_rejects_invalid_input(payload):
    repository = FakeTrustedContactRepository()
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/trusted-contacts", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert repository.contacts == []


@pytest.mark.asyncio
async def test_list_trusted_contacts_returns_empty_collection():
    repository = FakeTrustedContactRepository()
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/trusted-contacts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"contacts": [], "count": 0}


@pytest.mark.asyncio
async def test_list_trusted_contacts_orders_active_contacts_newest_first():
    repository = FakeTrustedContactRepository()
    now = datetime.now(timezone.utc)
    older = TrustedContact(
        id=uuid4(), name="Older", contact_method="email", contact_value="older@example.com",
        is_active=True, created_at=now - timedelta(minutes=2), updated_at=now - timedelta(minutes=2),
    )
    newer = TrustedContact(
        id=uuid4(), name="Newer", contact_method="phone", contact_value="+1234567890",
        is_active=True, created_at=now - timedelta(minutes=1), updated_at=now - timedelta(minutes=1),
    )
    inactive = TrustedContact(
        id=uuid4(), name="Inactive", contact_method="email", contact_value="inactive@example.com",
        is_active=False, created_at=now, updated_at=now,
    )
    repository.contacts.extend([older, newer, inactive])
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/trusted-contacts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [contact["name"] for contact in body["contacts"]] == ["Newer", "Older"]


@pytest.mark.asyncio
async def test_list_trusted_contacts_is_bounded_to_the_newest_active_contacts():
    repository = FakeTrustedContactRepository()
    now = datetime.now(timezone.utc)
    contacts = [
        TrustedContact(
            id=uuid4(),
            name=f"Contact {index}",
            contact_method="email",
            contact_value=f"contact{index}@example.com",
            is_active=True,
            created_at=now - timedelta(seconds=index),
            updated_at=now - timedelta(seconds=index),
        )
        for index in range(105)
    ]
    repository.contacts.extend(contacts)
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/trusted-contacts")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 100
    assert len(body["contacts"]) == 100
    assert body["contacts"][0]["name"] == "Contact 0"
    assert body["contacts"][-1]["name"] == "Contact 99"


@pytest.mark.asyncio
async def test_get_trusted_contact_and_unknown_contact():
    repository = FakeTrustedContactRepository()
    contact = TrustedContact(
        id=uuid4(), name="Asha", contact_method="email", contact_value="asha@example.com",
        is_active=True, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    repository.contacts.append(contact)
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            found = await client.get(f"/api/v1/trusted-contacts/{contact.id}")
            missing = await client.get(f"/api/v1/trusted-contacts/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert found.status_code == 200
    assert found.json()["id"] == str(contact.id)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_delete_deactivates_contact_and_repeated_delete_returns_not_found():
    repository = FakeTrustedContactRepository()
    contact = TrustedContact(
        id=uuid4(), name="Asha", contact_method="email", contact_value="asha@example.com",
        is_active=True, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    repository.contacts.append(contact)
    repository_override(repository)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            deleted = await client.delete(f"/api/v1/trusted-contacts/{contact.id}")
            repeated = await client.delete(f"/api/v1/trusted-contacts/{contact.id}")
    finally:
        app.dependency_overrides.clear()

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert repeated.status_code == 404
    assert contact.is_active is False
    assert repository.deactivated == [str(contact.id)]


def test_trusted_contact_migration_is_provider_neutral_and_has_no_user_foreign_key():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "0007_create_trusted_contacts.py"
    source = migration.read_text()

    assert 'revision: str = "0007_create_trusted_contacts"' in source
    assert 'down_revision: Union[str, None] = "0006_add_safe_trip_completion"' in source
    assert '"trusted_contacts"' in source
    assert "contact_method" in source
    assert "contact_value" in source
    assert "is_active" in source
    assert "ForeignKeyConstraint" not in source
    assert "twilio" not in source.lower()
    assert "provider" not in source.lower()
