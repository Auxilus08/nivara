from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import (
    get_safe_trip_check_in_repository,
    get_safe_trip_location_repository,
    get_safe_trip_repository,
    get_safe_trip_trusted_contact_repository,
    get_trusted_contact_repository,
)
from app.repositories.trip import SafeTripRepository
from app.repositories.trip_location import SafeTripLocationRepository
from app.repositories.trip_check_in import SafeTripCheckInRepository
from app.repositories.trip_trusted_contact import SafeTripTrustedContactRepository
from app.repositories.trusted_contact import TrustedContactRepository
from app.schemas.trip import (
    DeviationAssessment,
    SafeTripCreate,
    SafeTripLocationCreate,
    SafeTripLocationResponse,
    SafeTripCheckInResponse,
    SafeTripHistoryResponse,
    SafeTripResponse,
)
from app.schemas.trusted_contact import (
    SafeTripTrustedContactCreate,
    SafeTripTrustedContactListResponse,
    SafeTripTrustedContactResponse,
)
from app.core.config import get_settings
from app.services.trips import (
    SafeTripInvalidStateError,
    SafeTripLocationService,
    SafeTripCheckInService,
    SafeTripDeviationService,
    SafeTripNotFoundError,
    SafeTripService,
    SafeTripTrustedContactAlreadyExistsError,
    SafeTripTrustedContactNotFoundError,
    SafeTripTrustedContactService,
)

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.get("/history", response_model=SafeTripHistoryResponse)
async def get_safe_trip_history(
    repository: SafeTripRepository = Depends(get_safe_trip_repository),
) -> SafeTripHistoryResponse:
    return await SafeTripService(repository).history()


@router.get("/{trip_id}/trusted-contacts", response_model=SafeTripTrustedContactListResponse)
async def list_safe_trip_trusted_contacts(
    trip_id: UUID,
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    contact_repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
    association_repository: SafeTripTrustedContactRepository = Depends(get_safe_trip_trusted_contact_repository),
) -> SafeTripTrustedContactListResponse:
    try:
        return await SafeTripTrustedContactService(
            trip_repository, contact_repository, association_repository
        ).list(trip_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{trip_id}/trusted-contacts",
    response_model=SafeTripTrustedContactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_safe_trip_trusted_contact(
    trip_id: UUID,
    request: SafeTripTrustedContactCreate,
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    contact_repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
    association_repository: SafeTripTrustedContactRepository = Depends(get_safe_trip_trusted_contact_repository),
) -> SafeTripTrustedContactResponse:
    try:
        return await SafeTripTrustedContactService(
            trip_repository, contact_repository, association_repository
        ).attach(trip_id, request.trusted_contact_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripTrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SafeTripTrustedContactAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{trip_id}/trusted-contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_safe_trip_trusted_contact(
    trip_id: UUID,
    contact_id: UUID,
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    contact_repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
    association_repository: SafeTripTrustedContactRepository = Depends(get_safe_trip_trusted_contact_repository),
) -> Response:
    try:
        await SafeTripTrustedContactService(
            trip_repository, contact_repository, association_repository
        ).remove(trip_id, contact_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripTrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.post("/{trip_id}/complete", response_model=SafeTripResponse)
async def complete_safe_trip(
    trip_id: UUID,
    repository: SafeTripRepository = Depends(get_safe_trip_repository),
) -> SafeTripResponse:
    try:
        return await SafeTripService(repository).complete(trip_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{trip_id}/check-ins", response_model=SafeTripCheckInResponse, status_code=status.HTTP_201_CREATED)
async def record_safe_trip_check_in(
    trip_id: UUID,
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    check_in_repository: SafeTripCheckInRepository = Depends(get_safe_trip_check_in_repository),
) -> SafeTripCheckInResponse:
    try:
        return await SafeTripCheckInService(trip_repository, check_in_repository).record(trip_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{trip_id}/deviation", response_model=DeviationAssessment)
async def evaluate_safe_trip_deviation(
    trip_id: UUID,
    trip_repository: SafeTripRepository = Depends(get_safe_trip_repository),
    location_repository: SafeTripLocationRepository = Depends(get_safe_trip_location_repository),
) -> DeviationAssessment:
    try:
        settings = get_settings()
        return await SafeTripDeviationService(
            trip_repository,
            location_repository,
            settings.deviation_corridor_threshold_meters,
        ).evaluate_trip(trip_id)
    except SafeTripNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SafeTripInvalidStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
