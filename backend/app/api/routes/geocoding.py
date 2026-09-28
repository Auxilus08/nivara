from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.providers.routing import (
    GeocodingProviderConfigurationError,
    GeocodingProviderError,
    GeocodingProviderRateLimited,
    GeocodingProviderRequestFailed,
    GeocodingProviderResponseError,
    GeocodingProviderTimeout,
    OpenRouteServiceProvider,
    UnconfiguredGeocodingProvider,
)
from app.schemas.routes import DestinationSearchResponse
from app.services.geocoding import GeocodingService

router = APIRouter(prefix="/api/v1/geocoding", tags=["geocoding"])


async def get_geocoding_service() -> GeocodingService:
    settings = get_settings()
    if settings.routing_provider.lower() == "openrouteservice":
        return GeocodingService(OpenRouteServiceProvider(settings.routing_api_key))
    return GeocodingService(
        UnconfiguredGeocodingProvider(
            f"Geocoding provider '{settings.routing_provider}' is not supported."
        )
    )


@router.get("/search", response_model=DestinationSearchResponse)
async def search_destinations(
    query: Annotated[str, Query(alias="q", min_length=2, max_length=200)],
    service: GeocodingService = Depends(get_geocoding_service),
) -> DestinationSearchResponse:
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a destination to search.",
        )
    try:
        return await service.search(query)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except GeocodingProviderError as exc:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        if isinstance(exc, GeocodingProviderRateLimited):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, GeocodingProviderTimeout):
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif isinstance(exc, (GeocodingProviderRequestFailed, GeocodingProviderResponseError)):
            status_code = status.HTTP_502_BAD_GATEWAY
        elif isinstance(exc, GeocodingProviderConfigurationError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
