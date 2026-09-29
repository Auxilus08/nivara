import httpx
import pytest

from app.core.config import get_settings
from app.main import app


@pytest.mark.asyncio
async def test_demo_mode_provides_route_and_geocoding_without_database() -> None:
    settings = get_settings()
    previous = settings.demo_mode
    settings.demo_mode = True
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            geocoding = await client.get("/api/v1/geocoding/search", params={"q": "demo"})
            routes = await client.post(
                "/api/v1/routes",
                json={
                    "origin": {"latitude": 21.18, "longitude": 79.06},
                    "destination": {"latitude": 21.19, "longitude": 79.07},
                    "mode": "balanced",
                },
            )
        assert geocoding.status_code == 200
        assert geocoding.json()["results"]
        assert routes.status_code == 200
        assert len(routes.json()["routes"]) == 3
    finally:
        settings.demo_mode = previous
