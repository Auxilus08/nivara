import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_safe_places_query_filter_order_and_shape() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/safe-places/nearby", params={"latitude": 21.145, "longitude": 79.089, "radius": 1000, "category": "hospital"})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["resources"][0]["category"] == "hospital"
    assert body["resources"][0]["distance_meters"] >= 0
    assert body["resources"][0]["is_demo_resource"] is True
    assert "phone" not in body["resources"][0]


@pytest.mark.asyncio
async def test_safe_places_reject_invalid_coordinates_and_unbounded_radius() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/api/v1/safe-places/nearby", params={"latitude": 91, "longitude": 79})).status_code == 422
        assert (await client.get("/api/v1/safe-places/nearby", params={"latitude": 21, "longitude": 79, "radius": 50001})).status_code == 422


@pytest.mark.asyncio
async def test_privacy_defaults_and_update_do_not_expose_sensitive_data() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.patch("/api/v1/privacy/settings", json={"location_sharing_enabled": False, "trusted_contact_sharing_enabled": False, "emergency_sharing_enabled": False})
        initial = await client.get("/api/v1/privacy/settings")
        assert initial.status_code == 200
        assert initial.json()["location_sharing_enabled"] is False
        updated = await client.patch("/api/v1/privacy/settings", json={"location_sharing_enabled": True, "emergency_sharing_enabled": True})
    assert updated.status_code == 200
    body = updated.json()
    assert body["location_sharing_enabled"] is True
    assert body["emergency_sharing_enabled"] is True
    assert "latitude" not in body and "contact_value" not in body
