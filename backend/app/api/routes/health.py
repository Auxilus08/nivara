from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse
from app.services.health import get_health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, include_in_schema=True)
async def health() -> HealthResponse:
    return get_health(get_settings())


@router.get("/api/v1/health", response_model=HealthResponse, include_in_schema=True)
async def versioned_health() -> HealthResponse:
    return get_health(get_settings())
