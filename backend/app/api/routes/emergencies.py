from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_emergency_repository,
    get_safe_trip_location_repository,
    get_safe_trip_repository,
)
from app.models.emergency import EmergencyStatus
from app.repositories.emergency import EmergencyRepository
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.schemas.emergency import (
    EmergencyCreate,
    EmergencyResourceListResponse,
    EmergencyResponse,
)
from app.services.emergencies import (
    EmergencyDuplicateError,
    EmergencyInvalidStateError,
    EmergencyNotFoundError,
    EmergencyService,
    demo_emergency_resources,
)

router = APIRouter(prefix="/api/v1/emergencies", tags=["emergencies"])


@router.get("/resources", response_model=EmergencyResourceListResponse)
async def get_emergency_resources() -> EmergencyResourceListResponse:
    return demo_emergency_resources()


def service(
    emergency_repository: EmergencyRepository,
    trip_repository: SafeTripRepository,
    location_repository: SafeTripLocationRepository,
) -> EmergencyService:
    return EmergencyService(emergency_repository, trip_repository, location_repository)


@router.post("", response_model=EmergencyResponse, status_code=status.HTTP_201_CREATED)
async def create_emergency(
    request: EmergencyCreate,
    emergency_repository: EmergencyRepository = Depends(get_emergency_repository),
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    location_repository: SafeTripLocationRepository = Depends(get_safe_trip_location_repository),
) -> EmergencyResponse:
    try:
        return await service(emergency_repository, trip_repository, location_repository).create(request)
    except EmergencyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (EmergencyDuplicateError, EmergencyInvalidStateError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


async def transition_emergency(
    emergency_id: UUID,
    target: EmergencyStatus,
    emergency_repository: EmergencyRepository,
    trip_repository: SafeTripRepository,
    location_repository: SafeTripLocationRepository,
) -> EmergencyResponse:
    try:
        return await service(emergency_repository, trip_repository, location_repository).transition(
            emergency_id, target
        )
    except EmergencyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except EmergencyInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{emergency_id}/acknowledge", response_model=EmergencyResponse)
async def acknowledge_emergency(
    emergency_id: UUID,
    emergency_repository: EmergencyRepository = Depends(get_emergency_repository),
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    location_repository: SafeTripLocationRepository = Depends(get_safe_trip_location_repository),
) -> EmergencyResponse:
    return await transition_emergency(
        emergency_id, EmergencyStatus.ACKNOWLEDGED, emergency_repository, trip_repository, location_repository
    )


@router.post("/{emergency_id}/resolve", response_model=EmergencyResponse)
async def resolve_emergency(
    emergency_id: UUID,
    emergency_repository: EmergencyRepository = Depends(get_emergency_repository),
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    location_repository: SafeTripLocationRepository = Depends(get_safe_trip_location_repository),
) -> EmergencyResponse:
    return await transition_emergency(
        emergency_id, EmergencyStatus.RESOLVED, emergency_repository, trip_repository, location_repository
    )
