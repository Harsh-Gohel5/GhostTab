from typing import Literal

import jwt
from fastapi import FastAPI, Request
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ghosttab_api import __version__
from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.google_sources import router as google_sources_router
from ghosttab_api.routes import router
from ghosttab_api.slack_sources import router as slack_router


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["ghosttab-api"] = "ghosttab-api"
    version: str = __version__


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(
        title="GhostTab API",
        description="Prepare evidence-backed context for meetings and everyday work.",
        version=__version__,
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.environment != "production" else None,
    )
    app.state.settings = settings
    app.state.sessions = sessions(
        engine if engine is not None else make_engine(settings.database_url)
    )
    if settings.auth_mode == "local":
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "test"])
    else:
        app.state.jwks = jwt.PyJWKClient(
            settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json",
            cache_jwk_set=True,
            lifespan=300,
            timeout=5,
        )
    app.include_router(router)
    app.include_router(slack_router)
    app.include_router(google_sources_router)

    @app.middleware("http")
    async def private_responses(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/api/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        """Process liveness only; does not assert connector or worker readiness."""
        return HealthResponse()

    return app


app = create_app()
