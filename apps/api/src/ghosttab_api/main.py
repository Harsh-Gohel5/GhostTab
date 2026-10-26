from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from ghosttab_api import __version__
from ghosttab_api.config import Settings


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["ghosttab-api"] = "ghosttab-api"
    version: str = __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(
        title="GhostTab API",
        description="Prepare a grounded, current workspace for the next development task.",
        version=__version__,
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.environment != "production" else None,
    )

    @app.get("/api/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        """Process liveness only; does not assert connector or worker readiness."""
        return HealthResponse()

    return app


app = create_app()
