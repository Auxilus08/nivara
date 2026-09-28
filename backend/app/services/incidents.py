from collections import Counter
from datetime import datetime, timedelta, timezone
from math import cos, radians
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
from app.schemas.heatmap import HeatmapBounds, HeatmapPoint, HeatmapQuery, HeatmapResponse
from app.schemas.incident import IncidentReportCreate, IncidentSignalContext
from app.schemas.routes import RouteGeometry
from app.services.safety import SAFETY_DISCLAIMER, SafetyEngine


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
    def __init__(self, repository: IncidentRepository, safety_engine: SafetyEngine | None = None):
        self.repository = repository
        self.safety_engine = safety_engine or SafetyEngine()

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
        return self._signals_from_incidents(
            incidents=incidents,
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            as_of=effective_as_of,
        )

    async def get_route_contextual_signals(
        self,
        *,
        geometry: RouteGeometry,
        corridor_radius_meters: float,
        as_of: datetime | None = None,
    ) -> IncidentSignalContext:
        effective_as_of = as_of or datetime.now(timezone.utc)
        incidents = await self.repository.list_near_route(
            coordinates=geometry.coordinates,
            corridor_radius_meters=corridor_radius_meters,
            occurred_to=effective_as_of,
            limit=100,
        )
        latitude = sum(point.latitude for point in geometry.coordinates) / len(geometry.coordinates)
        longitude = sum(point.longitude for point in geometry.coordinates) / len(geometry.coordinates)
        return self._signals_from_incidents(
            incidents=incidents,
            latitude=latitude,
            longitude=longitude,
            radius_meters=corridor_radius_meters,
            as_of=effective_as_of,
            route_context=True,
        )

    def _signals_from_incidents(
        self,
        *,
        incidents: list[Incident],
        latitude: float,
        longitude: float,
        radius_meters: float,
        as_of: datetime,
        route_context: bool = False,
    ) -> IncidentSignalContext:
        recent_cutoff = as_of - timedelta(days=30)
        severity_counts = Counter(item.severity.value for item in incidents)
        category_counts = Counter(item.category.value for item in incidents)
        confidence_counts = Counter(item.confidence_level.value for item in incidents)
        notes = []
        if route_context:
            notes.append("incident indicators were collected within the configured route corridor")
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
            as_of=as_of,
            incident_count=len(incidents),
            recent_incident_count=sum(item.occurred_at >= recent_cutoff for item in incidents),
            severity_counts=dict(severity_counts),
            category_counts=dict(category_counts),
            confidence_level_counts=dict(confidence_counts),
            indicator_notes=notes,
        )

    async def get_heatmap(self, query: HeatmapQuery) -> HeatmapResponse:
        """Aggregate a bounded viewport into coarse cells assessed by SafetyEngine."""
        as_of = datetime.now(timezone.utc)
        incidents = await self.repository.list_in_bounds(
            min_latitude=query.min_latitude,
            min_longitude=query.min_longitude,
            max_latitude=query.max_latitude,
            max_longitude=query.max_longitude,
            occurred_to=as_of,
            limit=1000,
        )
        cells: dict[tuple[int, int], list[Incident]] = {}
        latitude_span = query.max_latitude - query.min_latitude
        longitude_span = query.max_longitude - query.min_longitude
        for incident in incidents:
            row = min(int((incident.latitude - query.min_latitude) / latitude_span * query.rows), query.rows - 1)
            column = min(int((incident.longitude - query.min_longitude) / longitude_span * query.columns), query.columns - 1)
            cells.setdefault((row, column), []).append(incident)

        points: list[HeatmapPoint] = []
        recent_cutoff = as_of - timedelta(days=self.safety_engine.config.recent_window_days)
        for (row, column), cell_incidents in sorted(cells.items()):
            center_latitude = query.min_latitude + ((row + 0.5) / query.rows) * latitude_span
            center_longitude = query.min_longitude + ((column + 0.5) / query.columns) * longitude_span
            cell_latitude_meters = latitude_span / query.rows * 111_320
            cell_longitude_meters = (
                longitude_span / query.columns * 111_320 * max(cos(radians(center_latitude)), 0.01)
            )
            context = IncidentSignalContext(
                latitude=center_latitude,
                longitude=center_longitude,
                radius_meters=max(min(cell_latitude_meters, cell_longitude_meters) / 2, 25),
                as_of=as_of,
                incident_count=len(cell_incidents),
                recent_incident_count=sum(item.occurred_at >= recent_cutoff for item in cell_incidents),
                severity_counts=dict(Counter(item.severity.value for item in cell_incidents)),
                category_counts=dict(Counter(item.category.value for item in cell_incidents)),
                confidence_level_counts=dict(
                    Counter(item.confidence_level.value for item in cell_incidents)
                ),
                indicator_notes=["incident-derived indicators aggregated in a coarse map cell"],
            )
            assessment = self.safety_engine.assess(context)
            points.append(
                HeatmapPoint(
                    latitude=center_latitude,
                    longitude=center_longitude,
                    risk_score=assessment.risk_score,
                    risk_level=assessment.risk_level,
                    incident_count=assessment.incident_count,
                    confidence=assessment.confidence,
                )
            )

        return HeatmapResponse(
            bounds=HeatmapBounds(
                min_latitude=query.min_latitude,
                min_longitude=query.min_longitude,
                max_latitude=query.max_latitude,
                max_longitude=query.max_longitude,
            ),
            rows=query.rows,
            columns=query.columns,
            points=points,
            incident_count=len(incidents),
            disclaimer=SAFETY_DISCLAIMER,
        )
