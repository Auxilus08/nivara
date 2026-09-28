from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.routes import router as routes_router
from app.api.routes.safety import router as safety_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(incidents_router)
api_router.include_router(routes_router)
api_router.include_router(safety_router)
