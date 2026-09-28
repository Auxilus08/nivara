from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.routing import (
    OpenRouteServiceProvider,
    RoutingProviderError,
    RoutingProviderRateLimited,
    RoutingProviderTimeout,
    UnconfiguredRoutingProvider,
)
from app.core.config import get_settings
from app.db.session import get_db_session
from app.repositories.incident import IncidentRepository
from app.schemas.routes import RouteRequest, RouteResponse
from app.services.incidents import IncidentService
from app.services.routes import RoutingService

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


async def get_routing_service(
    session: AsyncSession = Depends(get_db_session),
) -> RoutingService:
    settings = get_settings()
    context_provider = IncidentService(IncidentRepository(session))
    if settings.routing_provider.lower() == "openrouteservice":
        return RoutingService(
            OpenRouteServiceProvider(settings.routing_api_key),
            context_provider=context_provider,
            corridor_radius_meters=settings.route_corridor_radius_meters,
        )
    return RoutingService(
        UnconfiguredRoutingProvider(
            f"Routing provider '{settings.routing_provider}' is not supported."
        ),
        context_provider=context_provider,
        corridor_radius_meters=settings.route_corridor_radius_meters,
    )


@router.post("", response_model=RouteResponse)
async def calculate_routes(
    request: RouteRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteResponse:
    try:
        return await service.calculate_routes(request)
    except RoutingProviderError as exc:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        if isinstance(exc, RoutingProviderRateLimited):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, RoutingProviderTimeout):
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif exc.code in {"routing_provider_request_failed", "routing_provider_response_error"}:
            status_code = status.HTTP_502_BAD_GATEWAY
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": exc.code,
                "message": str(exc),
            },
        ) from exc
