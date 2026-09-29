from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.geocoding import router as geocoding_router
from app.api.routes.emergencies import router as emergencies_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.routes import router as routes_router
from app.api.routes.safety import router as safety_router
from app.api.routes.safe_places import router as safe_places_router
from app.api.routes.privacy import router as privacy_router
from app.api.routes.trips import router as trips_router
from app.api.routes.trusted_contacts import router as trusted_contacts_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Nivara API",
        description="Contextual safety-aware navigation and journey protection API.",
        version="0.1.0",
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    # Include concrete routers at the application boundary. This avoids
    # retaining nested router wrappers in FastAPI versions that do not flatten
    # them during ASGI dispatch.
    app.include_router(health_router)
    app.include_router(geocoding_router)
    app.include_router(emergencies_router)
    app.include_router(incidents_router)
    app.include_router(routes_router)
    app.include_router(safety_router)
    app.include_router(safe_places_router)
    app.include_router(privacy_router)
    app.include_router(trips_router)
    app.include_router(trusted_contacts_router)
    return app


app = create_app()
