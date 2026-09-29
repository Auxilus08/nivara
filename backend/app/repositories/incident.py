from datetime import datetime
from collections.abc import Sequence
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import Select, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import (
    ConfidenceLevel,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)
from app.schemas.routes import Coordinate


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()
        # Reports must survive the request-scoped session so a later route
        # request can include the newly submitted incident in its corridor
        # query.
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def get_by_id(self, incident_id: UUID) -> Incident | None:
        return await self.session.get(Incident, incident_id)

    async def list(
        self,
        *,
        category: IncidentCategory | None = None,
        severity: IncidentSeverity | None = None,
        status: IncidentStatus | None = None,
        confidence_level: ConfidenceLevel | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        radius_meters: float | None = None,
        limit: int = 50,
    ) -> list[Incident]:
        statement: Select[tuple[Incident]] = select(Incident)
        if category is not None:
            statement = statement.where(Incident.category == category)
        if severity is not None:
            statement = statement.where(Incident.severity == severity)
        if status is not None:
            statement = statement.where(Incident.status == status)
        if confidence_level is not None:
            statement = statement.where(Incident.confidence_level == confidence_level)
        if occurred_from is not None:
            statement = statement.where(Incident.occurred_at >= occurred_from)
        if occurred_to is not None:
            statement = statement.where(Incident.occurred_at <= occurred_to)
        if latitude is not None and longitude is not None and radius_meters is not None:
            point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            statement = statement.where(func.ST_DWithin(cast(Incident.location, Geography), cast(point, Geography), radius_meters))
        statement = statement.order_by(Incident.occurred_at.desc()).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_near_route(
        self,
        *,
        coordinates: Sequence[Coordinate],
        corridor_radius_meters: float,
        occurred_to: datetime | None = None,
        limit: int = 100,
    ) -> list[Incident]:
        """Return incidents within a PostGIS corridor around a route line."""
        if len(coordinates) < 2:
            return []

        line_wkt = "LINESTRING(" + ", ".join(
            f"{coordinate.longitude} {coordinate.latitude}" for coordinate in coordinates
        ) + ")"
        route_line = func.ST_GeomFromText(line_wkt, 4326)
        statement: Select[tuple[Incident]] = select(Incident).where(
            func.ST_DWithin(
                cast(Incident.location, Geography),
                cast(route_line, Geography),
                corridor_radius_meters,
            )
        )
        if occurred_to is not None:
            statement = statement.where(Incident.occurred_at <= occurred_to)
        statement = statement.order_by(Incident.occurred_at.desc()).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_in_bounds(
        self,
        *,
        min_latitude: float,
        min_longitude: float,
        max_latitude: float,
        max_longitude: float,
        occurred_to: datetime | None = None,
        limit: int = 1000,
    ) -> list[Incident]:
        """Return incidents in a bounded PostGIS viewport."""
        viewport = func.ST_MakeEnvelope(
            min_longitude,
            min_latitude,
            max_longitude,
            max_latitude,
            4326,
        )
        statement: Select[tuple[Incident]] = select(Incident).where(
            func.ST_Intersects(Incident.location, viewport)
        )
        if occurred_to is not None:
            statement = statement.where(Incident.occurred_at <= occurred_to)
        statement = statement.order_by(Incident.occurred_at.desc()).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
