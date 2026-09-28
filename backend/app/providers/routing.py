from dataclasses import dataclass, field
from math import isfinite
from typing import Protocol

import httpx

from app.schemas.routes import (
    Coordinate,
    DestinationSuggestion,
    RouteGeometry,
    RouteRequest,
)


class RoutingProviderError(Exception):
    """Base error for provider failures safe to map at the API boundary."""

    code = "routing_provider_error"


class RoutingProviderUnavailable(RoutingProviderError):
    """Raised when no concrete external routing adapter is configured."""

    code = "routing_provider_unavailable"


class RoutingProviderConfigurationError(RoutingProviderError):
    code = "routing_provider_configuration_error"


class RoutingProviderRateLimited(RoutingProviderError):
    code = "routing_provider_rate_limited"


class RoutingProviderTimeout(RoutingProviderError):
    code = "routing_provider_timeout"


class RoutingProviderRequestFailed(RoutingProviderError):
    code = "routing_provider_request_failed"


class RoutingProviderResponseError(RoutingProviderError):
    code = "routing_provider_response_error"


class GeocodingProviderError(Exception):
    """Base error for geocoding failures safe to map at the API boundary."""

    code = "geocoding_provider_error"


class GeocodingProviderUnavailable(GeocodingProviderError):
    code = "geocoding_provider_unavailable"


class GeocodingProviderConfigurationError(GeocodingProviderError):
    code = "geocoding_provider_configuration_error"


class GeocodingProviderRateLimited(GeocodingProviderError):
    code = "geocoding_provider_rate_limited"


class GeocodingProviderTimeout(GeocodingProviderError):
    code = "geocoding_provider_timeout"


class GeocodingProviderRequestFailed(GeocodingProviderError):
    code = "geocoding_provider_request_failed"


class GeocodingProviderResponseError(GeocodingProviderError):
    code = "geocoding_provider_response_error"


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

    def __init__(self, message: str | None = None):
        self.message = message or "No external routing provider is configured for this environment."

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        raise RoutingProviderUnavailable(self.message)


class UnconfiguredGeocodingProvider:
    name = "unconfigured"

    def __init__(self, message: str | None = None):
        self.message = message or "No external geocoding provider is configured for this environment."

    async def search(
        self, query: str, proximity: Coordinate | None = None
    ) -> list[DestinationSuggestion]:
        raise GeocodingProviderUnavailable(self.message)


class OpenRouteServiceProvider:
    """Adapter for the openrouteservice Directions GeoJSON API."""

    name = "openrouteservice"
    default_base_url = "https://api.openrouteservice.org"
    default_geocoding_base_url = "https://api.heigit.org"
    profile = "driving-car"

    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str = default_base_url,
        geocoding_base_url: str = default_geocoding_base_url,
        timeout_seconds: float = 10.0,
        client_factory=httpx.AsyncClient,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.geocoding_base_url = geocoding_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client_factory = client_factory

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        if not self.api_key:
            raise RoutingProviderConfigurationError(
                "The routing provider API key is not configured."
            )

        payload = {
            "coordinates": [
                [request.origin.longitude, request.origin.latitude],
                [request.destination.longitude, request.destination.latitude],
            ],
            "instructions": False,
            "alternative_routes": {
                "target_count": 3,
                "share_factor": 0.8,
                "weight_factor": 1.4,
            },
        }
        headers = {
            "Authorization": self.api_key,
            "Accept": "application/geo+json",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/v2/directions/{self.profile}/geojson"

        try:
            async with self.client_factory(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise RoutingProviderTimeout("The routing provider request timed out.") from exc
        except httpx.RequestError as exc:
            raise RoutingProviderRequestFailed(
                "The routing provider request could not be completed."
            ) from exc

        if response.status_code == 401 or response.status_code == 403:
            raise RoutingProviderConfigurationError(
                "The routing provider rejected the configured credentials."
            )
        if response.status_code == 429:
            raise RoutingProviderRateLimited(
                "The routing provider rate limit was reached."
            )
        if response.status_code >= 400:
            raise RoutingProviderRequestFailed(
                "The routing provider returned an HTTP error."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RoutingProviderResponseError(
                "The routing provider returned invalid JSON."
            ) from exc
        return self._normalize_geojson(data)

    async def search(
        self, query: str, proximity: Coordinate | None = None
    ) -> list[DestinationSuggestion]:
        if not self.api_key:
            raise GeocodingProviderConfigurationError(
                "The geocoding provider API key is not configured."
            )

        params: dict[str, str | int | float] = {"text": query, "size": 5}
        if proximity is not None:
            params["focus.point.lat"] = proximity.latitude
            params["focus.point.lon"] = proximity.longitude
        headers = {
            "Authorization": self.api_key,
            "Accept": "application/json",
        }
        url = f"{self.geocoding_base_url}/pelias/v1/search"

        try:
            async with self.client_factory(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            raise GeocodingProviderTimeout("The geocoding provider request timed out.") from exc
        except httpx.RequestError as exc:
            raise GeocodingProviderRequestFailed(
                "The geocoding provider request could not be completed."
            ) from exc

        if response.status_code == 401 or response.status_code == 403:
            raise GeocodingProviderConfigurationError(
                "The geocoding provider rejected the configured credentials."
            )
        if response.status_code == 429:
            raise GeocodingProviderRateLimited(
                "The geocoding provider rate limit was reached."
            )
        if response.status_code >= 400:
            raise GeocodingProviderRequestFailed(
                "The geocoding provider returned an HTTP error."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise GeocodingProviderResponseError(
                "The geocoding provider returned invalid JSON."
            ) from exc
        return self._normalize_geocoding(data)

    def _normalize_geojson(self, data: object) -> list[ProviderRoute]:
        if not isinstance(data, dict):
            raise RoutingProviderResponseError("The routing provider response shape was invalid.")
        features = data.get("features")
        if not isinstance(features, list) or not features:
            raise RoutingProviderResponseError("The routing provider returned no route geometry.")

        routes: list[ProviderRoute] = []
        for index, feature in enumerate(features):
            if not isinstance(feature, dict):
                raise RoutingProviderResponseError("The routing provider route feature was invalid.")
            geometry = feature.get("geometry")
            properties = feature.get("properties")
            if not isinstance(geometry, dict) or geometry.get("type") != "LineString":
                raise RoutingProviderResponseError("The routing provider geometry was not a LineString.")
            if not isinstance(properties, dict) or not isinstance(properties.get("summary"), dict):
                raise RoutingProviderResponseError("The routing provider route summary was missing.")

            coordinates = geometry.get("coordinates")
            summary = properties["summary"]
            distance = summary.get("distance")
            duration = summary.get("duration")
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                raise RoutingProviderResponseError("The routing provider geometry was incomplete.")
            if not isinstance(distance, (int, float)) or not isfinite(distance) or distance < 0:
                raise RoutingProviderResponseError("The routing provider distance was invalid.")
            if not isinstance(duration, (int, float)) or not isfinite(duration) or duration < 0:
                raise RoutingProviderResponseError("The routing provider duration was invalid.")

            normalized_coordinates = []
            for coordinate in coordinates:
                if (
                    not isinstance(coordinate, list)
                    or len(coordinate) < 2
                    or not isinstance(coordinate[0], (int, float))
                    or not isinstance(coordinate[1], (int, float))
                ):
                    raise RoutingProviderResponseError("The routing provider coordinate was invalid.")
                try:
                    normalized_coordinates.append(
                        Coordinate(latitude=coordinate[1], longitude=coordinate[0])
                    )
                except ValueError as exc:
                    raise RoutingProviderResponseError(
                        "The routing provider coordinate was out of range."
                    ) from exc

            routes.append(
                ProviderRoute(
                    provider_route_id=f"route-{index}",
                    distance_meters=float(distance),
                    estimated_duration_seconds=round(float(duration)),
                    geometry=RouteGeometry(coordinates=normalized_coordinates),
                    metadata={"profile": self.profile, "geometry_format": "geojson"},
                )
            )
        return routes

    def _normalize_geocoding(self, data: object) -> list[DestinationSuggestion]:
        if not isinstance(data, dict):
            raise GeocodingProviderResponseError("The geocoding provider response shape was invalid.")
        features = data.get("features")
        if not isinstance(features, list):
            raise GeocodingProviderResponseError("The geocoding provider results were invalid.")

        suggestions: list[DestinationSuggestion] = []
        for index, feature in enumerate(features[:5]):
            if not isinstance(feature, dict):
                raise GeocodingProviderResponseError("The geocoding provider result was invalid.")
            geometry = feature.get("geometry")
            properties = feature.get("properties")
            if (
                not isinstance(geometry, dict)
                or geometry.get("type") != "Point"
                or not isinstance(properties, dict)
            ):
                raise GeocodingProviderResponseError("The geocoding provider result shape was invalid.")
            coordinates = geometry.get("coordinates")
            label = properties.get("label")
            if (
                not isinstance(coordinates, list)
                or len(coordinates) < 2
                or not isinstance(coordinates[0], (int, float))
                or not isinstance(coordinates[1], (int, float))
                or not isinstance(label, str)
                or not label.strip()
            ):
                raise GeocodingProviderResponseError("The geocoding provider result fields were invalid.")
            try:
                coordinate = Coordinate(latitude=coordinates[1], longitude=coordinates[0])
            except ValueError as exc:
                raise GeocodingProviderResponseError(
                    "The geocoding provider returned an out-of-range coordinate."
                ) from exc
            provider_id = feature.get("id")
            suggestion_id = provider_id if isinstance(provider_id, str) and provider_id else f"geocode-{index}"
            suggestions.append(
                DestinationSuggestion(
                    suggestion_id=suggestion_id,
                    label=label.strip(),
                    coordinate=coordinate,
                )
            )
        return suggestions
