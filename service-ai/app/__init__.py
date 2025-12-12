from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .core.config import get_settings


def create_app() -> FastAPI:
    """
    Crea e configura l'istanza FastAPI dell'AI Service.
    """
    settings = get_settings()

    app = FastAPI(
        title="AI Service",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # CORS basato su ALLOWED_ORIGINS dal .env
    origins = settings.allowed_origins_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Registra i router (health, echo, e in futuro ai/*)
    app.include_router(api_router)

    return app
