from app.providers.routing import (
    ProviderRoute,
    RoutingProvider,
    RoutingProviderError,
)
from pydantic import ValidationError
from app.schemas.routes import RouteCandidate, RouteRequest, RouteResponse


class RoutingService:
    """Orchestrates provider calls and returns Nivara-owned route contracts."""

    def __init__(self, provider: RoutingProvider):
        self.provider = provider

    async def calculate_routes(self, request: RouteRequest) -> RouteResponse:
        try:
            provider_routes = await self.provider.route(request)
        except RoutingProviderError:
            raise
        except Exception as exc:  # provider adapters must not leak implementation errors
            raise RoutingProviderError("External routing provider request failed") from exc

        try:
            normalized_routes = [self._normalize_route(request, route) for route in provider_routes]
            return RouteResponse(mode=request.mode, routes=normalized_routes)
        except ValidationError as exc:
            raise RoutingProviderError("External routing provider returned invalid route data") from exc

    def _normalize_route(self, request: RouteRequest, route: ProviderRoute) -> RouteCandidate:
        return RouteCandidate(
            route_id=f"{self.provider.name}:{route.provider_route_id}",
            origin=request.origin,
            destination=request.destination,
            distance_meters=route.distance_meters,
            estimated_duration_seconds=route.estimated_duration_seconds,
            geometry=route.geometry,
            provider=self.provider.name,
            provider_metadata=route.metadata,
        )
