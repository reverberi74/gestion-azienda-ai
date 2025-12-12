from fastapi import APIRouter

from .v1.routes_health import router as health_router
from .v1.routes_echo import router as echo_router
from .v1.routes_ai import router as ai_router

api_router = APIRouter()

# Versione 1 delle API
api_router.include_router(health_router, prefix="/v1", tags=["health"])
api_router.include_router(echo_router, prefix="/v1", tags=["echo"])
api_router.include_router(ai_router, prefix="/v1", tags=["ai"])
