from datetime import datetime, timezone
from uuid import UUID, uuid4

from geoalchemy2.elements import WKTElement

from app.models.trip import SafeTrip, SafeTripCheckIn, SafeTripStatus
from app.models.trip import SafeTripLocation
from app.models.trusted_contact import TrustedContact
from app.models.trip_trusted_contact import SafeTripTrustedContact
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.repositories.trip_check_in import SafeTripCheckInRepository
from app.repositories.trip_trusted_contact import SafeTripTrustedContactRepository
from app.repositories.trusted_contact import TrustedContactRepository
from app.schemas.routes import Coordinate
from app.schemas.trip import (
    DeviationAssessment,
    SafeTripCreate,
    SafeTripHistoryItem,
    SafeTripHistoryResponse,
    SafeTripLocationCreate,
    SafeTripLocationResponse,
    SafeTripResponse,
    SafeTripCheckInResponse,
)
from app.schemas.trusted_contact import (
    SafeTripTrustedContactListResponse,
    SafeTripTrustedContactResponse,
    TrustedContactResponse,
)


class SafeTripNotFoundError(LookupError):
    """Raised when a requested trip does not exist."""


class SafeTripInvalidStateError(ValueError):
    """Raised when a trip cannot legally enter the requested state."""


class SafeTripTrustedContactAlreadyExistsError(ValueError):
    """Raised when a contact is already selected for a Safe Trip."""


class SafeTripTrustedContactNotFoundError(LookupError):
    """Raised when a requested Safe Trip/contact association does not exist."""


def location_to_response(location: SafeTripLocation) -> SafeTripLocationResponse:
    return SafeTripLocationResponse(
        id=location.id,
        trip_id=location.trip_id,
        latitude=location.latitude,
        longitude=location.longitude,
        recorded_at=location.recorded_at,
        received_at=location.received_at,
    )


def trip_to_response(trip: SafeTrip) -> SafeTripResponse:
    return SafeTripResponse(
        id=trip.id,
        selected_route_id=trip.selected_route_id,
        origin={"latitude": trip.origin_latitude, "longitude": trip.origin_longitude},
        destination={"latitude": trip.destination_latitude, "longitude": trip.destination_longitude},
        distance_meters=trip.route_distance_meters,
        estimated_duration_seconds=trip.route_duration_seconds,
        geometry={"coordinates": trip.route_geometry},
        expected_arrival_at=trip.expected_arrival_at,
        status=trip.status,
        started_at=trip.started_at,
        completed_at=trip.completed_at,
        created_at=trip.created_at,
    )


def trip_to_history_item(trip: SafeTrip) -> SafeTripHistoryItem:
    return SafeTripHistoryItem(
        id=trip.id,
        status=trip.status,
        created_at=trip.created_at,
        started_at=trip.started_at,
        completed_at=trip.completed_at,
        expected_arrival_at=trip.expected_arrival_at,
        origin={"latitude": trip.origin_latitude, "longitude": trip.origin_longitude},
        destination={"latitude": trip.destination_latitude, "longitude": trip.destination_longitude},
    )


class SafeTripService:
    def __init__(self, repository: SafeTripRepository):
        self.repository = repository

    async def create(self, request: SafeTripCreate) -> SafeTripResponse:
        expected_arrival = request.expected_arrival_at
        if expected_arrival <= datetime.now(timezone.utc):
            raise ValueError("expected_arrival_at must be in the future")
        trip = SafeTrip(
            id=uuid4(),
            selected_route_id=request.selected_route_id,
            origin_latitude=request.origin.latitude,
            origin_longitude=request.origin.longitude,
            destination_latitude=request.destination.latitude,
            destination_longitude=request.destination.longitude,
            route_distance_meters=request.distance_meters,
            route_duration_seconds=request.estimated_duration_seconds,
            route_geometry=[point.model_dump() for point in request.geometry.coordinates],
            expected_arrival_at=expected_arrival,
            status=SafeTripStatus.PLANNED.value,
            created_at=datetime.now(timezone.utc),
        )
        return trip_to_response(await self.repository.create(trip))

    async def start(self, trip_id: UUID) -> SafeTripResponse:
        trip = await self.repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status != SafeTripStatus.PLANNED.value:
            raise SafeTripInvalidStateError(
                f"Safe Trip cannot be started from status '{trip.status}'"
            )

        started_at = datetime.now(timezone.utc)
        trip.status = SafeTripStatus.ACTIVE.value
        trip.started_at = started_at
        return trip_to_response(await self.repository.update(trip))

    async def complete(self, trip_id: UUID) -> SafeTripResponse:
        trip = await self.repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status != SafeTripStatus.ACTIVE.value:
            raise SafeTripInvalidStateError(
                f"Safe Trip cannot be completed from status '{trip.status}'"
            )

        trip.status = SafeTripStatus.COMPLETED.value
        trip.completed_at = datetime.now(timezone.utc)
        return trip_to_response(await self.repository.update(trip))

    async def history(self) -> SafeTripHistoryResponse:
        trips = [trip_to_history_item(trip) for trip in await self.repository.list_history()]
        return SafeTripHistoryResponse(trips=trips, count=len(trips))


class SafeTripLocationService:
    def __init__(self, trip_repository: SafeTripRepository, location_repository: SafeTripLocationRepository):
        self.trip_repository = trip_repository
        self.location_repository = location_repository

    async def record(self, trip_id: UUID, request: SafeTripLocationCreate) -> SafeTripLocationResponse:
        trip = await self.trip_repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status != SafeTripStatus.ACTIVE.value:
            raise SafeTripInvalidStateError(
                f"Safe Trip cannot receive locations from status '{trip.status}'"
            )

        location = SafeTripLocation(
            id=uuid4(),
            trip_id=trip_id,
            latitude=request.latitude,
            longitude=request.longitude,
            location=WKTElement(f"POINT({request.longitude} {request.latitude})", srid=4326),
            recorded_at=request.recorded_at,
            received_at=datetime.now(timezone.utc),
        )
        return location_to_response(await self.location_repository.create(location))


def check_in_to_response(check_in: SafeTripCheckIn) -> SafeTripCheckInResponse:
    return SafeTripCheckInResponse(
        id=check_in.id,
        trip_id=check_in.trip_id,
        checked_in_at=check_in.checked_in_at,
    )


class SafeTripCheckInService:
    def __init__(self, trip_repository: SafeTripRepository, check_in_repository: SafeTripCheckInRepository):
        self.trip_repository = trip_repository
        self.check_in_repository = check_in_repository

    async def record(self, trip_id: UUID) -> SafeTripCheckInResponse:
        trip = await self.trip_repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status != SafeTripStatus.ACTIVE.value:
            raise SafeTripInvalidStateError(
                f"Safe Trip cannot accept check-ins from status '{trip.status}'"
            )

        check_in = SafeTripCheckIn(
            id=uuid4(),
            trip_id=trip_id,
            checked_in_at=datetime.now(timezone.utc),
        )
        return check_in_to_response(await self.check_in_repository.create(check_in))


def trip_trusted_contact_to_response(
    association: SafeTripTrustedContact, contact: TrustedContact
) -> SafeTripTrustedContactResponse:
    return SafeTripTrustedContactResponse(
        safe_trip_id=association.safe_trip_id,
        trusted_contact_id=association.trusted_contact_id,
        created_at=association.created_at,
        contact=TrustedContactResponse(
            id=contact.id,
            name=contact.name,
            contact_method=contact.contact_method,
            contact_value=contact.contact_value,
            is_active=contact.is_active,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        ),
    )


class SafeTripTrustedContactService:
    def __init__(
        self,
        trip_repository: SafeTripRepository,
        contact_repository: TrustedContactRepository,
        association_repository: SafeTripTrustedContactRepository,
    ):
        self.trip_repository = trip_repository
        self.contact_repository = contact_repository
        self.association_repository = association_repository

    async def list(self, trip_id: UUID) -> SafeTripTrustedContactListResponse:
        trip = await self.trip_repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        associations = await self.association_repository.list_for_trip(trip_id)
        contacts = [trip_trusted_contact_to_response(association, contact) for association, contact in associations]
        return SafeTripTrustedContactListResponse(contacts=contacts, count=len(contacts))

    async def attach(self, trip_id: UUID, contact_id: UUID) -> SafeTripTrustedContactResponse:
        trip = await self.trip_repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status == SafeTripStatus.COMPLETED.value:
            raise SafeTripInvalidStateError("Completed Safe Trips cannot be modified")

        contact = await self.contact_repository.get_active_by_id(contact_id)
        if contact is None:
            raise SafeTripTrustedContactNotFoundError("Trusted contact not found")
        if await self.association_repository.get(trip_id, contact_id) is not None:
            raise SafeTripTrustedContactAlreadyExistsError("Trusted contact is already selected for this Safe Trip")

        association = SafeTripTrustedContact(
            safe_trip_id=trip_id,
            trusted_contact_id=contact_id,
            created_at=datetime.now(timezone.utc),
        )
        persisted = await self.association_repository.create(association)
        return trip_trusted_contact_to_response(persisted, contact)

    async def remove(self, trip_id: UUID, contact_id: UUID) -> None:
        trip = await self.trip_repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status == SafeTripStatus.COMPLETED.value:
            raise SafeTripInvalidStateError("Completed Safe Trips cannot be modified")
        association = await self.association_repository.get(trip_id, contact_id)
        if association is None:
            raise SafeTripTrustedContactNotFoundError("Trusted contact association not found")
        await self.association_repository.delete(association)


class SafeTripDeviationService:
    def __init__(self, trip_repository: SafeTripRepository, location_repository: SafeTripLocationRepository, threshold_meters: float):
        self.trip_repository = trip_repository
        self.location_repository = location_repository
        self.threshold_meters = threshold_meters

    async def evaluate_trip(self, trip_id: UUID) -> DeviationAssessment:
        trip = await self.trip_repository.get_by_id(trip_id)
        if trip is None:
            raise SafeTripNotFoundError("Safe Trip not found")
        if trip.status != SafeTripStatus.ACTIVE.value:
            raise SafeTripInvalidStateError(
                f"Safe Trip deviation cannot be evaluated from status '{trip.status}'"
            )

        location = await self.location_repository.get_latest_for_trip(trip_id)
        if location is None:
            raise SafeTripInvalidStateError("Safe Trip has no recorded location to evaluate")

        coordinates = [Coordinate.model_validate(point) for point in trip.route_geometry]
        distance = await self.location_repository.distance_from_route_meters(location, coordinates)
        deviated = distance > self.threshold_meters
        if deviated:
            explanation = "The latest recorded location is outside the configured route corridor."
        else:
            explanation = "The latest recorded location is within the configured route corridor."
        return DeviationAssessment(
            trip_id=trip_id,
            deviated=deviated,
            distance_from_route_meters=round(distance, 2),
            threshold_meters=self.threshold_meters,
            based_on_location_id=location.id,
            evaluated_at=datetime.now(timezone.utc),
            explanation=explanation,
        )
