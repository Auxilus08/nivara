from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_safe_trip_location_repository, get_safe_trip_repository
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.schemas.trip import SafeTripCreate, SafeTripLocationCreate, SafeTripLocationResponse, SafeTripResponse
from app.services.trips import (
    SafeTripInvalidStateError,
    SafeTripLocationService,
    SafeTripNotFoundError,
    SafeTripService,
)

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.post("", response_model=SafeTripResponse, status_code=status.HTTP_201_CREATED)
async def create_safe_trip(
    request: SafeTripCreate,
    repository: SafeTripRepository = Depends(get_safe_trip_repository),
) -> SafeTripResponse:
    try:
        return await SafeTripService(repository).create(request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{trip_id}/start", response_model=SafeTripResponse)
async def start_safe_trip(
    trip_id: UUID,
    repository: SafeTripRepository = Depends(get_safe_trip_repository),
) -> SafeTripResponse:
    try:
        return await SafeTripService(repository).start(trip_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{trip_id}/locations", response_model=SafeTripLocationResponse, status_code=status.HTTP_201_CREATED)
async def record_safe_trip_location(
    trip_id: UUID,
    request: SafeTripLocationCreate,
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    location_repository: SafeTripLocationRepository = Depends(get_safe_trip_location_repository),
) -> SafeTripLocationResponse:
    try:
        return await SafeTripLocationService(trip_repository, location_repository).record(trip_id, request)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
