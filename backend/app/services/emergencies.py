from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.emergency import Emergency, EmergencyStatus
from app.repositories.emergency import EmergencyRepository
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.schemas.emergency import (
    EmergencyCreate,
    EmergencyResource,
    EmergencyResourceListResponse,
    EmergencyResponse,
)
from app.services.emergency_notifications import (
    EmergencyNotificationProvider,
    MockEmergencyNotificationProvider,
)
from app.models.trip import SafeTripStatus
from app.services.privacy import get_privacy_settings


class EmergencyNotFoundError(LookupError):
    pass


class EmergencyInvalidStateError(ValueError):
    pass


class EmergencyDuplicateError(ValueError):
    pass


def emergency_to_response(emergency: Emergency) -> EmergencyResponse:
    return EmergencyResponse(
        id=emergency.id,
        trip_id=emergency.trip_id,
        status=emergency.status,
        emergency_type=emergency.emergency_type,
        latitude=emergency.latitude,
        longitude=emergency.longitude,
        created_at=emergency.created_at,
        acknowledged_at=emergency.acknowledged_at,
        resolved_at=emergency.resolved_at,
        sharing_status=(
            "demo_notification_only"
            if (get_privacy_settings().emergency_sharing_enabled and get_privacy_settings().trusted_contact_sharing_enabled)
            else "sharing_disabled"
        ),
    )


class EmergencyService:
    def __init__(
        self,
        repository: EmergencyRepository,
        trip_repository: SafeTripRepository,
        location_repository: SafeTripLocationRepository,
        notification_provider: EmergencyNotificationProvider | None = None,
    ):
        self.repository = repository
        self.trip_repository = trip_repository
        self.location_repository = location_repository
        self.notification_provider = notification_provider or MockEmergencyNotificationProvider()

    async def create(self, request: EmergencyCreate) -> EmergencyResponse:
        latitude, longitude = request.latitude, request.longitude
        if request.trip_id is not None:
            trip = await self.trip_repository.get_by_id(request.trip_id)
            if trip is None:
                raise EmergencyNotFoundError("Safe Trip not found")
            if trip.status != SafeTripStatus.ACTIVE.value:
                raise EmergencyInvalidStateError("SOS can only be activated for an active Safe Trip")
            if await self.repository.get_active_for_trip(request.trip_id) is not None:
                raise EmergencyDuplicateError("An active emergency already exists for this Safe Trip")
            latest = await self.location_repository.get_latest_for_trip(request.trip_id)
            if latest is not None:
                latitude, longitude = latest.latitude, latest.longitude

        emergency = Emergency(
            id=uuid4(),
            trip_id=request.trip_id,
            status=EmergencyStatus.ACTIVE.value,
            emergency_type=request.emergency_type,
            latitude=latitude,
            longitude=longitude,
            created_at=datetime.now(timezone.utc),
        )
        persisted = await self.repository.create(emergency)
        privacy = get_privacy_settings()
        # The current prototype has no authenticated contact lookup. Keep the
        # provider deterministic and pass no contact identifiers unless both
        # explicit sharing controls are enabled; never claim delivery.
        contact_ids: list[UUID] = []
        sharing_status = "demo_notification_only" if privacy.emergency_sharing_enabled else "sharing_disabled"
        if not privacy.trusted_contact_sharing_enabled:
            sharing_status = "sharing_disabled"
        await self.notification_provider.notify(persisted, contact_ids)
        return emergency_to_response(persisted)

    async def transition(self, emergency_id: UUID, target: EmergencyStatus) -> EmergencyResponse:
        emergency = await self.repository.get_by_id(emergency_id)
        if emergency is None:
            raise EmergencyNotFoundError("Emergency not found")
        allowed = {
            EmergencyStatus.ACTIVE.value: {EmergencyStatus.ACKNOWLEDGED, EmergencyStatus.RESOLVED},
            EmergencyStatus.ACKNOWLEDGED.value: {EmergencyStatus.RESOLVED},
            EmergencyStatus.RESOLVED.value: set(),
        }
        if target not in allowed.get(emergency.status, set()):
            raise EmergencyInvalidStateError(
                f"Emergency cannot transition from '{emergency.status}' to '{target.value}'"
            )
        now = datetime.now(timezone.utc)
        emergency.status = target.value
        if target == EmergencyStatus.ACKNOWLEDGED:
            emergency.acknowledged_at = now
        else:
            emergency.resolved_at = now
        return emergency_to_response(await self.repository.update(emergency))


def demo_emergency_resources() -> EmergencyResourceListResponse:
    resources = [
        EmergencyResource(
            id="demo-local-emergency-services",
            category="emergency_services",
            name="Local emergency services (demo)",
            description="Demo resource placeholder. No phone number or live dispatch integration is configured.",
        ),
        EmergencyResource(
            id="demo-nearby-medical-assistance",
            category="medical_assistance",
            name="Nearby medical assistance (demo)",
            description="Demo resource placeholder for future verified resource discovery.",
        ),
        EmergencyResource(
            id="demo-trusted-contact-workflow",
            category="trusted_contacts",
            name="Configured trusted contacts (demo)",
            description="Future workflow placeholder. Selecting contacts does not send a message in this demo.",
        ),
    ]
    return EmergencyResourceListResponse(
        resources=resources,
        count=len(resources),
        disclaimer="These are synthetic demo resource placeholders; no emergency dispatch or contact delivery is performed.",
    )
