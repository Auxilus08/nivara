from typing import Protocol

from app.providers.routing import (
    ProviderRoute,
    RoutingProvider,
    RoutingProviderError,
)
from pydantic import ValidationError
from app.schemas.routes import RouteCandidate, RouteRequest, RouteResponse
from app.services.route_comparison import COMPARISON_DISCLAIMER, RouteComparisonService
from app.services.safety import SafetyEngine


class RouteContextProvider(Protocol):
    async def get_route_contextual_signals(self, *, geometry, corridor_radius_meters):
        """Return database-independent incident signals for a route corridor."""


class RoutingService:
    """Orchestrates provider calls and returns Nivara-owned route contracts."""

    def __init__(
        self,
        provider: RoutingProvider,
        *,
        context_provider: RouteContextProvider | None = None,
        safety_engine: SafetyEngine | None = None,
        comparison_service: RouteComparisonService | None = None,
        corridor_radius_meters: float = 100.0,
    ):
        self.provider = provider
        self.context_provider = context_provider
        self.safety_engine = safety_engine or SafetyEngine()
        self.comparison_service = comparison_service or RouteComparisonService()
        self.corridor_radius_meters = corridor_radius_meters

    async def calculate_routes(self, request: RouteRequest) -> RouteResponse:
        try:
            provider_routes = await self.provider.route(request)
        except RoutingProviderError:
            raise
        except Exception as exc:  # provider adapters must not leak implementation errors
            raise RoutingProviderError("External routing provider request failed") from exc

        try:
            normalized_routes = [self._normalize_route(request, route) for route in provider_routes]
            enriched_routes = await self._enrich_with_safety(normalized_routes)
            compared_routes, selected_route_id = self.comparison_service.compare(
                enriched_routes, request.mode
            )
            comparison_explanation = (
                COMPARISON_DISCLAIMER
                if all(route.safety_assessment is not None for route in compared_routes)
                else compared_routes[0].comparison_explanation
                if compared_routes
                else COMPARISON_DISCLAIMER
            )
            return RouteResponse(
                mode=request.mode,
                routes=compared_routes,
                selected_route_id=selected_route_id,
                comparison_explanation=comparison_explanation,
            )
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

    async def _enrich_with_safety(self, routes: list[RouteCandidate]) -> list[RouteCandidate]:
        if self.context_provider is None:
            return routes
        enriched: list[RouteCandidate] = []
        for route in routes:
            if route.geometry is None:
                enriched.append(route)
                continue
            context = await self.context_provider.get_route_contextual_signals(
                geometry=route.geometry,
                corridor_radius_meters=self.corridor_radius_meters,
            )
            enriched.append(
                route.model_copy(update={"safety_assessment": self.safety_engine.assess(context)})
            )
        return enriched
