import httpx
import pytest

from app.api.routes.geocoding import get_geocoding_service
from app.main import app
from app.providers.routing import (
    GeocodingProviderConfigurationError,
    GeocodingProviderRateLimited,
    GeocodingProviderRequestFailed,
    GeocodingProviderResponseError,
    GeocodingProviderTimeout,
    OpenRouteServiceProvider,
)
from app.schemas.routes import Coordinate
from app.services.geocoding import GeocodingService


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, url, *, params, headers):
        self.request = (url, params, headers)
        if self.error:
            raise self.error
        return self.response


def provider_with(response=None, error=None, api_key="test-secret"):
    client = FakeClient(response=response, error=error)
    provider = OpenRouteServiceProvider(
        api_key,
        base_url="https://provider.test",
        geocoding_base_url="https://geocoder.test",
        client_factory=lambda **kwargs: client,
    )
    return provider, client


def geocode_payload():
    return {
        "features": [
            {
                "id": "venue.1",
                "geometry": {"type": "Point", "coordinates": [77.5946, 12.9716]},
                "properties": {"label": "Nivara Square, Bengaluru"},
            }
        ]
    }


@pytest.mark.asyncio
async def test_openrouteservice_geocoding_normalizes_result_and_coordinate_order():
    provider, client = provider_with(FakeResponse(payload=geocode_payload()))

    results = await provider.search("Nivara Square", Coordinate(latitude=12.97, longitude=77.59))

    assert results[0].label == "Nivara Square, Bengaluru"
    assert results[0].coordinate.latitude == 12.9716
    assert results[0].coordinate.longitude == 77.5946
    assert client.request[0] == "https://geocoder.test/pelias/v1/search"
    assert client.request[1]["text"] == "Nivara Square"
    assert client.request[1]["size"] == 5
    assert client.request[1]["focus.point.lat"] == 12.97
    assert client.request[1]["focus.point.lon"] == 77.59
    assert client.request[2]["Authorization"] == "test-secret"


@pytest.mark.asyncio
async def test_geocoding_returns_empty_result_without_fabricating_destinations():
    provider, _ = provider_with(FakeResponse(payload={"features": []}))

    assert await provider.search("No such destination") == []


@pytest.mark.asyncio
async def test_geocoding_service_trims_query_and_bounds_results():
    class Provider:
        async def search(self, query, proximity=None):
            assert query == "Library"
            from app.schemas.routes import Coordinate, DestinationSuggestion

            return [
                DestinationSuggestion(
                    suggestion_id=str(index),
                    label=f"Library {index}",
                    coordinate=Coordinate(latitude=12 + index / 100, longitude=77),
                )
                for index in range(10)
            ]

    response = await GeocodingService(Provider()).search("  Library  ")

    assert response.count == 5
    assert [item.suggestion_id for item in response.results] == ["0", "1", "2", "3", "4"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type",
    [GeocodingProviderTimeout, GeocodingProviderRateLimited],
)
async def test_geocoding_provider_transport_errors_are_normalized(error_type):
    status_code = 429 if error_type is GeocodingProviderRateLimited else 200
    error = None if status_code == 429 else httpx.ReadTimeout("secret timeout")
    provider, _ = provider_with(FakeResponse(status_code=status_code), error=error)
    if status_code == 429:
        provider, _ = provider_with(FakeResponse(status_code=429))

    with pytest.raises(error_type):
        await provider.search("Library")


@pytest.mark.asyncio
async def test_geocoding_provider_rejects_missing_key_and_malformed_response_without_leaking_secret():
    provider, _ = provider_with(FakeResponse(payload={"not_features": []}), api_key=None)
    with pytest.raises(GeocodingProviderConfigurationError) as error:
        await provider.search("Library")
    assert "test-secret" not in str(error.value)

    provider, _ = provider_with(FakeResponse(payload={"features": [{"geometry": {}}]}))
    with pytest.raises(GeocodingProviderResponseError):
        await provider.search("Library")


@pytest.mark.asyncio
async def test_geocoding_provider_http_failure_is_normalized():
    provider, _ = provider_with(FakeResponse(status_code=500, payload={"error": "private"}))

    with pytest.raises(GeocodingProviderRequestFailed, match="HTTP error"):
        await provider.search("Library")


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["", " ", "x", "a" * 201])
async def test_geocoding_api_rejects_invalid_query(query):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/geocoding/search", params={"q": query})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_geocoding_api_returns_provider_neutral_contract():
    class Provider:
        async def search(self, query, proximity=None):
            from app.schemas.routes import Coordinate, DestinationSuggestion

            return [
                DestinationSuggestion(
                    suggestion_id="one",
                    label="Library, Bengaluru",
                    coordinate=Coordinate(latitude=12.9716, longitude=77.5946),
                )
            ]

    async def override_service():
        return GeocodingService(Provider())

    app.dependency_overrides[get_geocoding_service] = override_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/geocoding/search", params={"q": "Library"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "suggestion_id": "one",
                "label": "Library, Bengaluru",
                "coordinate": {"latitude": 12.9716, "longitude": 77.5946},
            }
        ],
        "count": 1,
    }


@pytest.mark.asyncio
async def test_geocoding_api_returns_empty_no_result_contract():
    class Provider:
        async def search(self, query, proximity=None):
            return []

    async def override_service():
        return GeocodingService(Provider())

    app.dependency_overrides[get_geocoding_service] = override_service
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/geocoding/search", params={"q": "Nowhere"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"results": [], "count": 0}
