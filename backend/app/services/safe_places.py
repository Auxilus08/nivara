from math import asin, cos, radians, sin, sqrt

from app.schemas.safe_places import (
    NearbySafePlaceQuery,
    SafePlaceCategory,
    SafePlaceListResponse,
    SafePlaceResponse,
)

_DEMO_RESOURCES = (
    ("demo-hospital", "Nearby medical assistance (demo)", SafePlaceCategory.HOSPITAL, 21.1458, 79.0882),
    ("demo-police", "Local police assistance (demo)", SafePlaceCategory.POLICE_STATION, 21.1491, 79.0910),
    ("demo-petrol", "Petrol pump assistance point (demo)", SafePlaceCategory.PETROL_PUMP, 21.1422, 79.0845),
    ("demo-hotel", "Hotel assistance point (demo)", SafePlaceCategory.HOTEL, 21.1510, 79.0860),
    ("demo-business", "Open business assistance point (demo)", SafePlaceCategory.OPEN_BUSINESS, 21.1470, 79.0940),
)

_FALLBACK_RESOURCE_TEMPLATES = (
    ("hospital", "Synthetic demo medical assistance resource"),
    ("police_station", "Synthetic demo police assistance resource"),
    ("petrol_pump", "Synthetic demo petrol assistance resource"),
    ("hotel", "Synthetic demo hotel assistance resource"),
    ("open_business", "Synthetic demo open-business assistance resource"),
)


def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius = 6_371_000
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return earth_radius * 2 * asin(sqrt(a))


def nearby_resources(query: NearbySafePlaceQuery) -> SafePlaceListResponse:
    resources = []
    for resource_id, name, category, latitude, longitude in _DEMO_RESOURCES:
        if query.category is not None and category != query.category:
            continue
        distance = _distance_meters(query.latitude, query.longitude, latitude, longitude)
        if distance <= query.radius:
            resources.append(SafePlaceResponse(id=resource_id, name=name, category=category, latitude=latitude, longitude=longitude, distance_meters=round(distance, 1)))
    resources.sort(key=lambda resource: (resource.distance_meters, resource.id))
    if not resources:
        # This provider is intentionally deterministic demo data. Keep the
        # demo useful when the user's real location is outside the fixed
        # Nagpur sample cluster by placing clearly-labelled synthetic points
        # around the requested coordinate. These are not real establishments.
        fallback_templates = _FALLBACK_RESOURCE_TEMPLATES
        if query.category is not None:
            fallback_templates = tuple(
                item for item in fallback_templates if item[0] == query.category.value
            )
        offset_meters = min(max(query.radius * 0.2, 50), 1000)
        for index, (category, name) in enumerate(fallback_templates):
            bearing_factor = index - (len(fallback_templates) - 1) / 2
            latitude = query.latitude + (offset_meters / 111_000) * (0.35 + abs(bearing_factor) * 0.08)
            longitude = query.longitude + (offset_meters / (111_000 * max(cos(radians(query.latitude)), 0.1))) * bearing_factor * 0.35
            distance = _distance_meters(query.latitude, query.longitude, latitude, longitude)
            resources.append(
                SafePlaceResponse(
                    id=f"demo-nearby-{category}",
                    name=name,
                    category=SafePlaceCategory(category),
                    latitude=latitude,
                    longitude=longitude,
                    distance_meters=round(distance, 1),
                )
            )
        resources.sort(key=lambda resource: (resource.distance_meters, resource.id))
    return SafePlaceListResponse(
        resources=resources,
        count=len(resources),
        disclaimer="These are synthetic demo resources, not verified real-world establishments or a guarantee of safety.",
    )
