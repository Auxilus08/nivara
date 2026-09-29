import httpx
import pytest
from pydantic import ValidationError

from app.main import app
from app.api.routes.routes import get_routing_service
from app.providers.routing import (
    OpenRouteServiceProvider,
    ProviderRoute,
    RoutingProviderConfigurationError,
    RoutingProviderError,
    RoutingProviderRateLimited,
    RoutingProviderTimeout,
)
from app.schemas.routes import Coordinate, RouteGeometry, RouteMode, RouteRequest
from app.services.routes import RoutingService


ORIGIN = Coordinate(latitude=12.9716, longitude=77.5946)
DESTINATION = Coordinate(latitude=12.9352, longitude=77.6245)


class FakeRoutingProvider:
    name = "fake-provider"

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        return [
            ProviderRoute(
                provider_route_id="candidate-1",
                distance_meters=4200,
                estimated_duration_seconds=900,
                geometry=RouteGeometry(coordinates=[request.origin, request.destination]),
                metadata={"profile": request.mode.value},
            )
        ]


class FailingRoutingProvider:
    name = "failing-provider"

    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        raise RoutingProviderError("provider timed out")


def test_route_request_validates_coordinates_and_modes():
    request = RouteRequest(origin=ORIGIN, destination=DESTINATION, mode=RouteMode.SAFETY_PRIORITY)

    assert request.mode == RouteMode.SAFETY_PRIORITY
    assert request.origin == ORIGIN

    with pytest.raises(ValidationError):
        RouteRequest(
            origin={"latitude": 91, "longitude": 0},
            destination=DESTINATION,
        )
    with pytest.raises(ValidationError):
        RouteRequest(origin=ORIGIN, destination=ORIGIN)


@pytest.mark.asyncio
async def test_routing_service_normalizes_provider_response():
    response = await RoutingService(FakeRoutingProvider()).calculate_routes(
        RouteRequest(origin=ORIGIN, destination=DESTINATION, mode=RouteMode.BALANCED)
    )

    assert response.mode == RouteMode.BALANCED
    assert len(response.routes) == 1
    route = response.routes[0]
    assert route.route_id == "fake-provider:candidate-1"
    assert route.provider == "fake-provider"
    assert route.distance_meters == 4200
    assert route.geometry is not None
    assert route.provider_metadata == {"profile": "balanced"}
    assert route.safety_assessment is None


@pytest.mark.asyncio
async def test_fastest_route_response_preserves_mode_and_safety_assessment():
    class ContextProvider:
        async def get_route_contextual_signals(self, *, geometry, corridor_radius_meters):
            from app.schemas.incident import IncidentSignalContext
            from datetime import datetime, timezone

            return IncidentSignalContext(
                latitude=12.95,
                longitude=77.60,
                radius_meters=corridor_radius_meters,
                as_of=datetime.now(timezone.utc),
                incident_count=1,
                recent_incident_count=1,
                severity_counts={"medium": 1},
                category_counts={"theft": 1},
                confidence_level_counts={"unverified": 1},
                indicator_notes=["route corridor context"],
            )

    response = await RoutingService(
        FakeRoutingProvider(), context_provider=ContextProvider()
    ).calculate_routes(
        RouteRequest(origin=ORIGIN, destination=DESTINATION, mode=RouteMode.FASTEST)
    )

    assert response.mode == RouteMode.FASTEST
    assert response.selected_route_id == "fake-provider:candidate-1"
    assert response.routes[0].safety_assessment is not None
    assert response.routes[0].normalized_travel_score == 100
    assert response.routes[0].comparison_cost is not None
    assert "not a guarantee of safety" in response.comparison_explanation


@pytest.mark.asyncio
async def test_route_api_accepts_fastest_mode_and_returns_comparison_contract():
    async def override_service():
        return RoutingService(FakeRoutingProvider())

    app.dependency_overrides[get_routing_service] = override_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/routes",
                json={
                    "origin": ORIGIN.model_dump(),
                    "destination": DESTINATION.model_dump(),
                    "mode": "fastest",
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["mode"] == "fastest"
    assert body["selected_route_id"] == "fake-provider:candidate-1"
    assert body["routes"][0]["estimated_duration_seconds"] == 900
    assert body["routes"][0]["normalized_travel_score"] == 100
    assert body["routes"][0]["comparison_cost"] == 100


@pytest.mark.asyncio
async def test_route_api_accepts_balanced_mode_without_changing_contract():
    async def override_service():
        return RoutingService(FakeRoutingProvider())

    app.dependency_overrides[get_routing_service] = override_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/routes",
                json={
                    "origin": ORIGIN.model_dump(),
                    "destination": DESTINATION.model_dump(),
                    "mode": "balanced",
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["mode"] == "balanced"
    assert body["selected_route_id"] == "fake-provider:candidate-1"
    assert "comparison_explanation" in body


@pytest.mark.asyncio
async def test_route_api_accepts_safety_priority_mode_without_changing_contract():
    async def override_service():
        return RoutingService(FakeRoutingProvider())

    app.dependency_overrides[get_routing_service] = override_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/routes",
                json={
                    "origin": ORIGIN.model_dump(),
                    "destination": DESTINATION.model_dump(),
                    "mode": "safety_priority",
                },
            )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["mode"] == "safety_priority"
    assert body["selected_route_id"] == "fake-provider:candidate-1"
    assert body["routes"][0]["distance_meters"] == 4200
    assert body["routes"][0]["estimated_duration_seconds"] == 900
    assert body["routes"][0]["comparison_cost"] == 100


@pytest.mark.asyncio
async def test_routing_service_propagates_provider_failures_without_database_access():
    with pytest.raises(RoutingProviderError, match="provider timed out"):
        await RoutingService(FailingRoutingProvider()).calculate_routes(
            RouteRequest(origin=ORIGIN, destination=DESTINATION)
        )


@pytest.mark.asyncio
async def test_unexpected_provider_failure_is_mapped_to_safe_service_error():
    class BrokenProvider:
        name = "broken-provider"

        async def route(self, request: RouteRequest) -> list[ProviderRoute]:
            raise RuntimeError("private provider detail")

    with pytest.raises(RoutingProviderError, match="External routing provider request failed"):
        await RoutingService(BrokenProvider()).calculate_routes(
            RouteRequest(origin=ORIGIN, destination=DESTINATION)
        )


@pytest.mark.asyncio
async def test_invalid_provider_route_data_is_rejected():
    class InvalidProvider:
        name = "invalid-provider"

        async def route(self, request: RouteRequest) -> list[ProviderRoute]:
            return [
                ProviderRoute(
                    provider_route_id="invalid",
                    distance_meters=-1,
                    estimated_duration_seconds=100,
                )
            ]

    with pytest.raises(RoutingProviderError, match="invalid route data"):
        await RoutingService(InvalidProvider()).calculate_routes(
            RouteRequest(origin=ORIGIN, destination=DESTINATION)
        )


@pytest.mark.asyncio
async def test_openrouteservice_success_normalizes_geojson_and_preserves_coordinate_order():
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[77.5946, 12.9716], [77.6245, 12.9352]],
                        },
                        "properties": {"summary": {"distance": 4200.5, "duration": 901.4}},
                    }
                ],
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, json, headers):
            captured.update({"url": url, "json": json, "headers": headers})
            return FakeResponse()

    provider = OpenRouteServiceProvider(
        "test-secret",
        base_url="https://routing.example.test",
        client_factory=lambda **kwargs: FakeClient(),
    )
    routes = await provider.route(RouteRequest(origin=ORIGIN, destination=DESTINATION))

    assert captured["url"] == "https://routing.example.test/v2/directions/driving-car/geojson"
    assert captured["json"]["coordinates"] == [[77.5946, 12.9716], [77.6245, 12.9352]]
    assert captured["json"]["radiuses"] == [-1, 5000]
    assert captured["headers"]["Authorization"] == "test-secret"
    assert routes[0].distance_meters == 4200.5
    assert routes[0].estimated_duration_seconds == 901
    assert routes[0].geometry.coordinates[0] == ORIGIN
    assert routes[0].geometry.coordinates[1] == DESTINATION


@pytest.mark.asyncio
async def test_openrouteservice_missing_key_is_explicit_and_does_not_leak_credentials():
    provider = OpenRouteServiceProvider(None)

    with pytest.raises(RoutingProviderConfigurationError, match="API key") as error:
        await provider.route(RouteRequest(origin=ORIGIN, destination=DESTINATION))

    assert "Authorization" not in str(error.value)


@pytest.mark.asyncio
async def test_openrouteservice_malformed_response_is_rejected():
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"features": [{"geometry": {"type": "Point"}}]}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, json, headers):
            return FakeResponse()

    provider = OpenRouteServiceProvider("test-secret", client_factory=lambda **kwargs: FakeClient())
    with pytest.raises(RoutingProviderError, match="geometry"):
        await provider.route(RouteRequest(origin=ORIGIN, destination=DESTINATION))


@pytest.mark.asyncio
async def test_openrouteservice_http_rate_limit_is_mapped_without_response_leakage():
    class FakeResponse:
        status_code = 429

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, json, headers):
            return FakeResponse()

    provider = OpenRouteServiceProvider("test-secret", client_factory=lambda **kwargs: FakeClient())
    with pytest.raises(RoutingProviderRateLimited, match="rate limit") as error:
        await provider.route(RouteRequest(origin=ORIGIN, destination=DESTINATION))
    assert "test-secret" not in str(error.value)


@pytest.mark.asyncio
async def test_openrouteservice_timeout_is_normalized():
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, json, headers):
            raise httpx.ReadTimeout("provider timeout")

    provider = OpenRouteServiceProvider("test-secret", client_factory=lambda **kwargs: FakeClient())
    with pytest.raises(RoutingProviderTimeout, match="timed out"):
        await provider.route(RouteRequest(origin=ORIGIN, destination=DESTINATION))


@pytest.mark.asyncio
async def test_route_api_reports_unconfigured_external_provider():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/routes",
            json={
                "origin": ORIGIN.model_dump(),
                "destination": DESTINATION.model_dump(),
                "mode": "fastest",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "routing_provider_configuration_error"


@pytest.mark.asyncio
async def test_route_api_rejects_invalid_coordinates_before_provider_call():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/routes",
            json={
                "origin": {"latitude": 100, "longitude": 0},
                "destination": DESTINATION.model_dump(),
            },
        )

    assert response.status_code == 422
