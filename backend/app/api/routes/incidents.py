from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_incident_repository
from app.models.incident import ConfidenceLevel, IncidentCategory, IncidentSeverity, IncidentStatus
from app.repositories.incident import IncidentRepository
from app.schemas.incident import IncidentListResponse, IncidentReportCreate, IncidentResponse
from app.services.incidents import IncidentService, incident_to_response_data

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.post("/reports", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_community_report(
    report: IncidentReportCreate,
    repository: IncidentRepository = Depends(get_incident_repository),
) -> IncidentResponse:
    service = IncidentService(repository)
    incident = await service.create_community_report(report)
    return IncidentResponse.model_validate(incident_to_response_data(incident))


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    repository: IncidentRepository = Depends(get_incident_repository),
    category: IncidentCategory | None = None,
    severity: IncidentSeverity | None = None,
    status_filter: Annotated[IncidentStatus | None, Query(alias="status")] = None,
    confidence_level: ConfidenceLevel | None = None,
    occurred_from: datetime | None = None,
    occurred_to: datetime | None = None,
    latitude: Annotated[float | None, Query(ge=-90, le=90)] = None,
    longitude: Annotated[float | None, Query(ge=-180, le=180)] = None,
    radius_meters: Annotated[float | None, Query(ge=25, le=10000)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> IncidentListResponse:
    service = IncidentService(repository)
    supplied_location = [latitude is not None, longitude is not None, radius_meters is not None]
    if any(supplied_location) and not all(supplied_location):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="latitude, longitude, and radius_meters must be provided together",
        )
    incidents = await service.list_incidents(
        category=category,
        severity=severity,
        status=status_filter,
        confidence_level=confidence_level,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit,
    )
    return IncidentListResponse(
        items=[IncidentResponse.model_validate(incident_to_response_data(item)) for item in incidents],
        limit=limit,
        count=len(incidents),
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    repository: IncidentRepository = Depends(get_incident_repository),
) -> IncidentResponse:
    service = IncidentService(repository)
    incident = await service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentResponse.model_validate(incident_to_response_data(incident))
