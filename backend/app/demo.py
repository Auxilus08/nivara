"""Deterministic in-memory adapters for the local hackathon demonstration.

Demo mode is opt-in through ``NIVARA_DEMO_MODE=true``. Live mode continues to
use PostgreSQL/PostGIS and the configured external routing provider.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import cos, radians, sqrt
from uuid import UUID, uuid4

from app.models.emergency import Emergency, EmergencyStatus
from app.models.incident import Incident
from app.models.trip import SafeTrip, SafeTripCheckIn, SafeTripLocation
from app.models.trusted_contact import TrustedContact
from app.models.trusted_contact_sharing_preference import TrustedContactSharingPreference
from app.models.trip_trusted_contact import SafeTripTrustedContact
from app.providers.routing import ProviderRoute
from app.schemas.routes import Coordinate, DestinationSuggestion, RouteGeometry, RouteRequest
from scripts.seed_demo_data import build_demo_incidents


def _distance(a: Coordinate, b: Coordinate) -> float:
    lat_m = (b.latitude - a.latitude) * 111_320
    lon_m = (b.longitude - a.longitude) * 111_320 * cos(radians((a.latitude + b.latitude) / 2))
    return sqrt(lat_m * lat_m + lon_m * lon_m)


def _segment_distance(point: Coordinate, start: Coordinate, end: Coordinate) -> float:
    dx, dy = end.longitude - start.longitude, end.latitude - start.latitude
    if dx == 0 and dy == 0:
        return _distance(point, start)
    t = max(0.0, min(1.0, ((point.longitude - start.longitude) * dx + (point.latitude - start.latitude) * dy) / (dx * dx + dy * dy)))
    nearest = Coordinate(latitude=start.latitude + t * dy, longitude=start.longitude + t * dx)
    return _distance(point, nearest)


@dataclass
class DemoStore:
    incidents: list[Incident] = field(default_factory=build_demo_incidents)
    trips: dict[UUID, SafeTrip] = field(default_factory=dict)
    locations: list[SafeTripLocation] = field(default_factory=list)
    check_ins: list[SafeTripCheckIn] = field(default_factory=list)
    contacts: dict[UUID, TrustedContact] = field(default_factory=dict)
    preferences: dict[UUID, TrustedContactSharingPreference] = field(default_factory=dict)
    associations: dict[tuple[UUID, UUID], SafeTripTrustedContact] = field(default_factory=dict)
    emergencies: dict[UUID, Emergency] = field(default_factory=dict)


demo_store = DemoStore()


class DemoIncidentRepository:
    async def create(self, incident):
        now = datetime.now(timezone.utc)
        incident.reported_at = incident.reported_at or now
        incident.created_at = incident.created_at or now
        incident.updated_at = incident.updated_at or now
        demo_store.incidents.append(incident)
        return incident
    async def get_by_id(self, incident_id): return next((x for x in demo_store.incidents if x.id == incident_id), None)
    async def list(self, **filters):
        result = list(demo_store.incidents)
        for key in ("category", "severity", "status", "confidence_level"):
            value = filters.get(key)
            if value is not None: result = [x for x in result if getattr(x, key) == value]
        if filters.get("occurred_from") is not None: result = [x for x in result if x.occurred_at >= filters["occurred_from"]]
        if filters.get("occurred_to") is not None: result = [x for x in result if x.occurred_at <= filters["occurred_to"]]
        lat, lon, radius = filters.get("latitude"), filters.get("longitude"), filters.get("radius_meters")
        if lat is not None and lon is not None and radius is not None:
            center = Coordinate(latitude=lat, longitude=lon)
            result = [x for x in result if _distance(center, Coordinate(latitude=x.latitude, longitude=x.longitude)) <= radius]
        return sorted(result, key=lambda x: x.occurred_at, reverse=True)[:filters.get("limit", 50)]
    async def list_near_route(self, *, coordinates, corridor_radius_meters, occurred_to=None, limit=100):
        result = []
        for incident in demo_store.incidents:
            if occurred_to and incident.occurred_at > occurred_to: continue
            point = Coordinate(latitude=incident.latitude, longitude=incident.longitude)
            if min(_segment_distance(point, a, b) for a, b in zip(coordinates, coordinates[1:])) <= corridor_radius_meters: result.append(incident)
        return sorted(result, key=lambda x: x.occurred_at, reverse=True)[:limit]
    async def list_in_bounds(self, *, min_latitude, min_longitude, max_latitude, max_longitude, occurred_to=None, limit=1000):
        return [x for x in demo_store.incidents if min_latitude <= x.latitude <= max_latitude and min_longitude <= x.longitude <= max_longitude and (occurred_to is None or x.occurred_at <= occurred_to)][:limit]


class DemoRoutingProvider:
    name = "demo"
    async def route(self, request: RouteRequest) -> list[ProviderRoute]:
        origin, destination = request.origin, request.destination
        distance = _distance(origin, destination)
        mid = Coordinate(latitude=(origin.latitude + destination.latitude) / 2, longitude=(origin.longitude + destination.longitude) / 2)
        offsets = ((0.0, 0.0), (0.003, -0.003), (-0.003, 0.003))
        routes = []
        for index, (lat_offset, lon_offset) in enumerate(offsets, 1):
            via = Coordinate(latitude=mid.latitude + lat_offset, longitude=mid.longitude + lon_offset)
            points = [origin, destination] if index == 1 else [origin, via, destination]
            length = sum(_distance(a, b) for a, b in zip(points, points[1:]))
            routes.append(ProviderRoute(provider_route_id=f"demo-{index}", distance_meters=round(max(length, distance), 1), estimated_duration_seconds=max(60, round(max(length, distance) / 8)), geometry=RouteGeometry(coordinates=points), metadata={"source": "synthetic_demo"}))
        return routes


class DemoGeocodingProvider:
    name = "demo"
    async def search(self, query: str, proximity=None) -> list[DestinationSuggestion]:
        return [DestinationSuggestion(suggestion_id="demo-destination", label=f"Demo destination for {query.strip()}", coordinate=Coordinate(latitude=21.18, longitude=79.06))]


class DemoSafeTripRepository:
    async def create(self, item): demo_store.trips[item.id] = item; return item
    async def get_by_id(self, item_id): return demo_store.trips.get(item_id)
    async def list_history(self): return sorted(demo_store.trips.values(), key=lambda x: x.created_at, reverse=True)
    async def update(self, item): demo_store.trips[item.id] = item; return item


class DemoLocationRepository:
    async def create(self, item): demo_store.locations.append(item); return item
    async def get_latest_for_trip(self, trip_id):
        items = [x for x in demo_store.locations if x.trip_id == trip_id]
        return max(items, key=lambda x: x.recorded_at, default=None)
    async def distance_from_route_meters(self, location, coordinates):
        return min(_segment_distance(Coordinate(latitude=location.latitude, longitude=location.longitude), a, b) for a, b in zip(coordinates, coordinates[1:]))


class DemoCheckInRepository:
    async def create(self, item): demo_store.check_ins.append(item); return item


class DemoContactRepository:
    async def create(self, item): demo_store.contacts[item.id] = item; return item
    async def update(self, item): demo_store.contacts[item.id] = item; return item
    async def list_active(self): return [x for x in demo_store.contacts.values() if x.is_active]
    async def get_active_by_id(self, item_id):
        item = demo_store.contacts.get(item_id); return item if item and item.is_active else None
    async def deactivate(self, item): item.is_active = False; return item


class DemoPreferenceRepository:
    async def get_by_contact_id(self, contact_id): return demo_store.preferences.get(contact_id)
    async def create(self, item): demo_store.preferences[item.trusted_contact_id] = item; return item
    async def update(self, item): demo_store.preferences[item.trusted_contact_id] = item; return item


class DemoAssociationRepository:
    async def get(self, trip_id, contact_id): return demo_store.associations.get((trip_id, contact_id))
    async def create(self, item): demo_store.associations[(item.safe_trip_id, item.trusted_contact_id)] = item; return item
    async def list_for_trip(self, trip_id):
        return [(a, demo_store.contacts[a.trusted_contact_id]) for a in demo_store.associations.values() if a.safe_trip_id == trip_id and demo_store.contacts[a.trusted_contact_id].is_active]
    async def delete(self, item): demo_store.associations.pop((item.safe_trip_id, item.trusted_contact_id), None)


class DemoEmergencyRepository:
    async def create(self, item): demo_store.emergencies[item.id] = item; return item
    async def get_by_id(self, item_id): return demo_store.emergencies.get(item_id)
    async def get_active_for_trip(self, trip_id): return next((x for x in demo_store.emergencies.values() if x.trip_id == trip_id and x.status in {EmergencyStatus.ACTIVE.value, EmergencyStatus.ACKNOWLEDGED.value}), None)
    async def update(self, item): demo_store.emergencies[item.id] = item; return item
