from datetime import datetime, timezone
from uuid import uuid4

from app.models.trip import SafeTrip, SafeTripStatus
from app.repositories.trip import SafeTripRepository
from app.schemas.trip import SafeTripCreate, SafeTripResponse


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
