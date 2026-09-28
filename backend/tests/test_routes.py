import httpx
import pytest
from pydantic import ValidationError

from app.main import app
from app.providers.routing import ProviderRoute, RoutingProviderError
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
    assert response.json()["detail"]["code"] == "routing_provider_unavailable"


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
