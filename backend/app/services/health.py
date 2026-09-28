from app.core.config import Settings
from app.schemas.health import HealthResponse


def get_health(settings: Settings) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        database=("configured" if settings.database_url else "not_configured"),
    )
