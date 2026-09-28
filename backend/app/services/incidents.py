from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from geoalchemy2.elements import WKTElement

from app.models.incident import (
    ConfidenceLevel,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.repositories.incident import IncidentRepository
from app.schemas.incident import IncidentReportCreate, IncidentSignalContext


def calculate_initial_confidence(source: IncidentSource) -> tuple[ConfidenceLevel, list[str]]:
    if source == IncidentSource.COMMUNITY_REPORT:
        return ConfidenceLevel.UNVERIFIED, ["single community report", "not yet corroborated"]
    if source in {IncidentSource.OFFICIAL_REPORT, IncidentSource.VERIFIED_PARTNER}:
        return ConfidenceLevel.HIGHER_CONFIDENCE, [f"source type: {source.value}"]
    return ConfidenceLevel.CORROBORATED, [f"source type: {source.value}"]


def incident_to_response_data(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "category": incident.category,
        "description": incident.description,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "occurred_at": incident.occurred_at,
        "reported_at": incident.reported_at,
        "severity": incident.severity,
        "source": incident.source,
        "status": incident.status,
        "confidence": {
            "level": incident.confidence_level,
            "corroboration_count": incident.corroboration_count,
            "factors": incident.confidence_factors,
        },
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
    }


class IncidentService:
    def __init__(self, repository: IncidentRepository):
        self.repository = repository

    async def create_community_report(self, report: IncidentReportCreate) -> Incident:
        occurred_at = report.occurred_at or datetime.now(timezone.utc)
        confidence, factors = calculate_initial_confidence(IncidentSource.COMMUNITY_REPORT)
        incident = Incident(
            id=uuid4(),
            category=report.category,
            description=report.description,
            latitude=report.latitude,
            longitude=report.longitude,
            location=WKTElement(f"POINT({report.longitude} {report.latitude})", srid=4326),
            occurred_at=occurred_at,
            severity=report.severity,
            source=IncidentSource.COMMUNITY_REPORT,
            confidence_level=confidence,
            corroboration_count=0,
            status=IncidentStatus.UNVERIFIED,
            confidence_factors=factors,
        )
        return await self.repository.create(incident)

    async def get_incident(self, incident_id: UUID) -> Incident | None:
        return await self.repository.get_by_id(incident_id)

    async def list_incidents(self, **filters) -> list[Incident]:
        return await self.repository.list(**filters)

    async def get_contextual_signals(
        self, *, latitude: float, longitude: float, radius_meters: float, as_of: datetime | None = None
    ) -> IncidentSignalContext:
        effective_as_of = as_of or datetime.now(timezone.utc)
        incidents = await self.repository.list(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            occurred_to=effective_as_of,
            limit=100,
        )
        recent_cutoff = effective_as_of - timedelta(days=30)
        severity_counts = Counter(item.severity.value for item in incidents)
        category_counts = Counter(item.category.value for item in incidents)
        confidence_counts = Counter(item.confidence_level.value for item in incidents)
        notes = []
        if incidents:
            notes.append(f"{len(incidents)} incident-derived indicators in the requested area")
        else:
            notes.append("limited incident activity detected in the requested area")
        if any(item.confidence_level == ConfidenceLevel.UNVERIFIED for item in incidents):
            notes.append("includes unverified community reports")
        return IncidentSignalContext(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            as_of=effective_as_of,
            incident_count=len(incidents),
            recent_incident_count=sum(item.occurred_at >= recent_cutoff for item in incidents),
            severity_counts=dict(severity_counts),
            category_counts=dict(category_counts),
            confidence_level_counts=dict(confidence_counts),
            indicator_notes=notes,
        )
