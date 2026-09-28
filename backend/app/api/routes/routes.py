from fastapi import APIRouter, Depends, HTTPException, status

from app.providers.routing import (
    RoutingProviderError,
    UnconfiguredRoutingProvider,
)
from app.schemas.routes import RouteRequest, RouteResponse
from app.services.routes import RoutingService

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


async def get_routing_service() -> RoutingService:
    # A concrete provider adapter will be selected here once the provider is
    # deliberately chosen. Returning an explicit unavailable error is safer
    # than silently fabricating route data.
    return RoutingService(UnconfiguredRoutingProvider())


@router.post("", response_model=RouteResponse)
async def calculate_routes(
    request: RouteRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteResponse:
    try:
        return await service.calculate_routes(request)
    except RoutingProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "routing_provider_unavailable",
                "message": str(exc),
            },
        ) from exc
