from datetime import datetime, timezone
from uuid import UUID, uuid4

from geoalchemy2.elements import WKTElement

from app.models.trip import SafeTrip, SafeTripStatus
from app.models.trip import SafeTripLocation
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.schemas.trip import (
    SafeTripCreate,
    SafeTripLocationCreate,
    SafeTripLocationResponse,
    SafeTripResponse,
)


class SafeTripNotFoundError(LookupError):
    """Raised when a requested trip does not exist."""


class SafeTripInvalidStateError(ValueError):
    """Raised when a trip cannot legally enter the requested state."""


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
        created_at=trip.created_at,
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
