from fastapi import APIRouter, Query

from app.schemas.safe_places import NearbySafePlaceQuery, SafePlaceCategory, SafePlaceListResponse
from app.services.safe_places import nearby_resources

router = APIRouter(prefix="/api/v1/safe-places", tags=["safe-places"])


@router.get("/nearby", response_model=SafePlaceListResponse)
async def get_nearby_safe_places(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=5000, gt=0, le=50000),
    category: SafePlaceCategory | None = Query(default=None),
) -> SafePlaceListResponse:
    return nearby_resources(NearbySafePlaceQuery(latitude=latitude, longitude=longitude, radius=radius, category=category))
