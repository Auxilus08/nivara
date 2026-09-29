from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_safe_trip_repository
from app.repositories.trip import SafeTripRepository
from app.schemas.trip import SafeTripCreate, SafeTripResponse
from app.services.trips import SafeTripService

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

