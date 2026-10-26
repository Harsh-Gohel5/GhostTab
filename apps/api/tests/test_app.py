import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from ghosttab_api.config import Settings
from ghosttab_api.main import create_app


def get(path: str, environment: str = "test"):
    async def request():
        async with AsyncClient(
            transport=ASGITransport(app=create_app(Settings(environment=environment))),
            base_url="http://test",
        ) as client:
            return await client.get(path)

    return asyncio.run(request())


def test_health_contract():
    response = get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ghosttab-api", "version": "0.1.0"}


def test_development_exposes_api_schema():
    assert get("/api/docs").status_code == 200
    assert "/api/health" in get("/api/openapi.json").json()["paths"]


@pytest.mark.parametrize("path", ["/api/docs", "/api/openapi.json", "/redoc"])
def test_production_disables_documentation(path):
    assert get(path, "production").status_code == 404


def test_invalid_environment_fails_configuration():
    with pytest.raises(ValidationError):
        Settings(environment="prodution")
