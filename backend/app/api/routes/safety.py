from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from app.api.dependencies import get_incident_repository
from app.repositories.incident import IncidentRepository
from app.schemas.heatmap import HeatmapQuery, HeatmapResponse
from app.services.incidents import IncidentService

router = APIRouter(prefix="/api/v1/safety", tags=["safety"])


async def get_heatmap_query(
    min_latitude: Annotated[float, Query(ge=-90, le=90)],
    min_longitude: Annotated[float, Query(ge=-180, le=180)],
    max_latitude: Annotated[float, Query(ge=-90, le=90)],
    max_longitude: Annotated[float, Query(ge=-180, le=180)],
    rows: Annotated[int, Query(ge=2, le=12)] = 8,
    columns: Annotated[int, Query(ge=2, le=12)] = 8,
) -> HeatmapQuery:
    try:
        return HeatmapQuery(
            min_latitude=min_latitude,
            min_longitude=min_longitude,
            max_latitude=max_latitude,
            max_longitude=max_longitude,
            rows=rows,
            columns=columns,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The heatmap viewport bounds are invalid or exceed the supported range.",
        ) from exc


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    query: HeatmapQuery = Depends(get_heatmap_query),
    repository: IncidentRepository = Depends(get_incident_repository),
) -> HeatmapResponse:
    return await IncidentService(repository).get_heatmap(query)
