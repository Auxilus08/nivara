from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.trusted_contact import TrustedContact, TrustedContactMethod
from app.models.trusted_contact_sharing_preference import TrustedContactSharingPreference
from app.repositories.trusted_contact import (
    TrustedContactRepository,
    TrustedContactSharingPreferenceRepository,
)
from app.schemas.trusted_contact import (
    TrustedContactCreate,
    TrustedContactListResponse,
    TrustedContactResponse,
    TrustedContactSharingPreferencePatch,
    TrustedContactSharingPreferenceResponse,
    TrustedContactUpdate,
)


class TrustedContactNotFoundError(LookupError):
    """Raised when an active trusted contact does not exist."""


def contact_to_response(contact: TrustedContact) -> TrustedContactResponse:
    return TrustedContactResponse(
        id=contact.id,
        name=contact.name,
        contact_method=contact.contact_method,
        contact_value=contact.contact_value,
        is_active=contact.is_active,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


class TrustedContactService:
    def __init__(self, repository: TrustedContactRepository):
        self.repository = repository

    async def create(self, request: TrustedContactCreate) -> TrustedContactResponse:
        now = datetime.now(timezone.utc)
        contact = TrustedContact(
            id=uuid4(),
            name=request.name,
            contact_method=request.contact_method.value,
            contact_value=request.contact_value,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        return contact_to_response(await self.repository.create(contact))

    async def list(self) -> TrustedContactListResponse:
        contacts = [contact_to_response(contact) for contact in await self.repository.list_active()]
        return TrustedContactListResponse(contacts=contacts, count=len(contacts))

    async def update(self, contact_id: UUID, request: TrustedContactUpdate) -> TrustedContactResponse:
        contact = await self.repository.get_active_by_id(contact_id)
        if contact is None:
            raise TrustedContactNotFoundError("Trusted contact not found")

        fields = request.model_fields_set
        validated = TrustedContactCreate(
            name=request.name if "name" in fields else contact.name,
            contact_method=(
                request.contact_method
                if "contact_method" in fields
                else TrustedContactMethod(contact.contact_method)
            ),
            contact_value=request.contact_value if "contact_value" in fields else contact.contact_value,
        )
        contact.name = validated.name
        contact.contact_method = validated.contact_method.value
        contact.contact_value = validated.contact_value
        contact.updated_at = datetime.now(timezone.utc)
        return contact_to_response(await self.repository.update(contact))

    async def get(self, contact_id: UUID) -> TrustedContactResponse:
        contact = await self.repository.get_active_by_id(contact_id)
        if contact is None:
            raise TrustedContactNotFoundError("Trusted contact not found")
        return contact_to_response(contact)

    async def delete(self, contact_id: UUID) -> None:
        contact = await self.repository.get_active_by_id(contact_id)
        if contact is None:
            raise TrustedContactNotFoundError("Trusted contact not found")
        await self.repository.deactivate(contact)


def sharing_preference_to_response(
    preference: TrustedContactSharingPreference,
) -> TrustedContactSharingPreferenceResponse:
    return TrustedContactSharingPreferenceResponse(
        trusted_contact_id=preference.trusted_contact_id,
        allow_trip_status=preference.allow_trip_status,
        allow_location=preference.allow_location,
        allow_emergency=preference.allow_emergency,
        created_at=preference.created_at,
        updated_at=preference.updated_at,
    )


class TrustedContactSharingPreferenceService:
    def __init__(
        self,
        contact_repository: TrustedContactRepository,
        preference_repository: TrustedContactSharingPreferenceRepository,
    ):
        self.contact_repository = contact_repository
        self.preference_repository = preference_repository

    async def get(self, contact_id: UUID) -> TrustedContactSharingPreferenceResponse:
        contact = await self.contact_repository.get_active_by_id(contact_id)
        if contact is None:
            raise TrustedContactNotFoundError("Trusted contact not found")

        preference = await self.preference_repository.get_by_contact_id(contact_id)
        if preference is None:
            now = datetime.now(timezone.utc)
            preference = await self.preference_repository.create(
                TrustedContactSharingPreference(
                    id=uuid4(),
                    trusted_contact_id=contact_id,
                    allow_trip_status=False,
                    allow_location=False,
                    allow_emergency=False,
                    created_at=now,
                    updated_at=now,
                )
            )
        return sharing_preference_to_response(preference)

    async def update(
        self, contact_id: UUID, request: TrustedContactSharingPreferencePatch
    ) -> TrustedContactSharingPreferenceResponse:
        contact = await self.contact_repository.get_active_by_id(contact_id)
        if contact is None:
            raise TrustedContactNotFoundError("Trusted contact not found")

        preference = await self.preference_repository.get_by_contact_id(contact_id)
        if preference is None:
            values = request.model_dump(exclude_unset=True)
            now = datetime.now(timezone.utc)
            preference = TrustedContactSharingPreference(
                id=uuid4(),
                trusted_contact_id=contact_id,
                allow_trip_status=values.get("allow_trip_status", False),
                allow_location=values.get("allow_location", False),
                allow_emergency=values.get("allow_emergency", False),
                created_at=now,
                updated_at=now,
            )
            preference = await self.preference_repository.create(preference)
        else:
            values = request.model_dump(exclude_unset=True)
            for field in ("allow_trip_status", "allow_location", "allow_emergency"):
                if field in values:
                    setattr(preference, field, values[field])
            preference.updated_at = datetime.now(timezone.utc)
            preference = await self.preference_repository.update(preference)
        return sharing_preference_to_response(preference)
