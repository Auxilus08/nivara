from dataclasses import dataclass, field
from typing import Protocol

from app.schemas.routes import (
    Coordinate,
    DestinationSuggestion,
    RouteGeometry,
    RouteRequest,
)


class RoutingProviderError(Exception):
    """Base error for provider failures safe to map at the API boundary."""


class RoutingProviderUnavailable(RoutingProviderError):
    """Raised when no concrete external routing adapter is configured."""


@dataclass(frozen=True)
class ProviderRoute:
    """Normalized provider output expected from a concrete adapter."""

    provider_route_id: str
    distance_meters: float
    estimated_duration_seconds: int
    geometry: RouteGeometry | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class RoutingProvider(Protocol):
    name: str

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        """Return provider routes already converted to the normalized shape."""


class GeocodingProvider(Protocol):
    name: str

    async def search(
        self, query: str, proximity: Coordinate | None = None
    ) -> list[DestinationSuggestion]:
        """Return provider-neutral destination suggestions."""


class UnconfiguredRoutingProvider:
    name = "unconfigured"

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        raise RoutingProviderUnavailable(
            "No external routing provider is configured for this environment."
        )
