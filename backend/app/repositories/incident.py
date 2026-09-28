from datetime import datetime
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


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        await self.session.flush()
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
