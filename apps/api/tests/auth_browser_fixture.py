"""Disposable auth UI rehearsal at 8011. No real Supabase, email or model calls.

Fictional sign-in: demo@example.test / demo-password. Production JWT verification
is NOT changed; this fixture alone supplies a local synthetic token verifier.
"""

import asyncio
import html
import secrets
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import jwt
import uvicorn
from connector_samples import SampleModel
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ghosttab_api.auth import Principal, current_user
from ghosttab_api.auth_providers import provider_status
from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.main import create_app
from ghosttab_api.models import Base, Budget
from ghosttab_api.readiness import touch_worker
from ghosttab_api.worker import run_once


def create_auth_fixture(folder, *, dist=None):
    # HTTP is allowed only in this isolated fixture. Real settings require HTTPS.
    settings = Settings(
        _env_file=None,
        environment="test",
        synthetic_demo=True,
        allow_model_requests=True,
        model_api_key="synthetic-fixture-only",
        database_url=f"sqlite:///{Path(folder).as_posix()}/auth.db",
    ).model_copy(
        update={
            "auth_mode": "supabase",
            "supabase_url": "http://127.0.0.1:8011",
            "supabase_publishable_key": "synthetic-public-key",
            "frontend_url": "http://127.0.0.1:8011",
        }
    )
    engine = make_engine(settings.database_url)
    Base.metadata.create_all(engine)
    factory = sessions(engine)
    with factory.begin() as session:
        session.add(Budget(id=1, charged_microusd=0))
    app = create_app(settings, engine=engine)
    app.dependency_overrides[provider_status] = lambda: {"google": "enabled"}
    secret = secrets.token_hex(32)
    profile_a = {
        "id": "synthetic-auth-owner",
        "aud": "authenticated",
        "role": "authenticated",
        "email": "demo@example.test",
        "email_confirmed_at": "2026-10-29T00:00:00Z",
        "created_at": "2026-10-29T00:00:00Z",
        "app_metadata": {"provider": "email"},
        "user_metadata": {"full_name": "Fictional User"},
        "identities": [],
    }

    profiles = {
        "demo@example.test": profile_a,
        "other@example.test": {
            **profile_a,
            "id": "synthetic-other-owner",
            "email": "other@example.test",
            "user_metadata": {"full_name": "Other Fictional User"},
        },
    }
    state = {"logout_failure": False, "refresh_failure": "none", "tasks_delay_ms": 0}
    refreshes = {"synthetic-refresh-" + p["id"]: p for p in profiles.values()}
    app.state.fixture = state

    class Scenario(BaseModel):
        logout_failure: bool = False
        refresh_failure: Literal["none", "rejected", "temporary"] = "none"
        tasks_delay_ms: int = Field(default=0, ge=0, le=5000)

    @app.post("/synthetic/scenario")
    def scenario(body: Scenario):
        state.update(body.model_dump())
        return state

    @app.middleware("http")
    async def delayed_tasks(request, call_next):
        touch_worker(factory, "synthetic-auth-fixture")
        response = await call_next(request)
        if request.method == "POST" and request.url.path.endswith("/prepare"):
            # Explicit fake client: the fixture never submits inference.
            run_once(factory, settings, SampleModel())
        if request.url.path == "/api/tasks":
            await asyncio.sleep(state["tasks_delay_ms"] / 1000)
        return response

    def token(profile=profile_a):
        return jwt.encode(
            {
                "sub": profile["id"],
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
                "role": "authenticated",
            },
            secret,
            algorithm="HS256",
        )

    def synthetic_user(request: Request):
        header = request.headers.get("authorization", "")
        try:
            claims = jwt.decode(
                header.removeprefix("Bearer "),
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(401, "Synthetic session required") from exc
        return Principal(claims["sub"])

    app.dependency_overrides[current_user] = synthetic_user

    @app.post("/auth/v1/token")
    async def signin(request: Request):
        body = await request.json()
        if request.query_params.get("grant_type") == "refresh_token":
            if state["refresh_failure"] != "none":
                rejected = state["refresh_failure"] == "rejected"
                return JSONResponse(
                    {
                        "msg": "Synthetic refresh unavailable",
                        "error_code": "refresh_token_not_found",
                    },
                    status_code=400 if rejected else 503,
                )
            profile = refreshes.get(body.get("refresh_token"))
        else:
            profile = (
                profiles.get(body.get("email")) if body.get("password") == "demo-password" else None
            )
        if profile is None:
            return JSONResponse({"msg": "Invalid fictional credentials"}, status_code=400)
        return {
            "access_token": token(profile),
            "refresh_token": "synthetic-refresh-" + profile["id"],
            "expires_in": 3600,
            "token_type": "bearer",
            "user": profile,
        }

    @app.get("/auth/v1/authorize")
    def google_authorize(request: Request):
        if (
            request.query_params.get("provider") != "google"
            or request.query_params.get("redirect_to") != "http://127.0.0.1:8011/"
        ):
            raise HTTPException(400, "Unsupported synthetic sign-in request")
        return RedirectResponse(
            "http://127.0.0.1:8011/#access_token="
            + token()
            + "&refresh_token=synthetic-refresh-synthetic-auth-owner&type=signup"
            + "&expires_in=3600&token_type=bearer",
            status_code=303,
        )

    @app.post("/auth/v1/signup")
    async def signup(request: Request):
        body = await request.json()
        profile_a["user_metadata"] = {
            "full_name": str(body.get("data", {}).get("full_name", "Fictional User"))[:80]
        }
        return {**profile_a, "confirmation_sent_at": "2026-10-29T00:00:00Z"}

    @app.post("/auth/v1/recover")
    @app.post("/auth/v1/resend")
    def email_request():
        return {}

    @app.get("/auth/v1/user")
    @app.put("/auth/v1/user")
    def user(request: Request):
        owner = synthetic_user(request).id
        return next(p for p in profiles.values() if p["id"] == owner)

    @app.post("/auth/v1/logout")
    def logout():
        if state["logout_failure"]:
            return JSONResponse({"msg": "Synthetic logout unavailable"}, status_code=503)
        return Response(status_code=204)

    @app.get("/synthetic-recovery")
    def recovery():
        url = (
            "http://127.0.0.1:8011/?auth=recovery#access_token="
            + token()
            + "&refresh_token=synthetic-refresh-synthetic-auth-owner&type=recovery"
            + "&expires_in=3600&token_type=bearer"
        )
        return HTMLResponse(
            '<p>Synthetic recovery only. No email was sent.</p><a href="'
            + html.escape(url)
            + '">Open synthetic recovery link</a>'
        )

    dist = dist if dist is not None else Path(__file__).resolve().parents[3] / "apps/web/dist"
    app.mount("/", StaticFiles(directory=dist, html=True))
    return app


def main():
    with TemporaryDirectory(prefix="ghosttab-auth-qa-") as folder:
        app = create_auth_fixture(folder)
        try:
            uvicorn.run(app, host="127.0.0.1", port=8011, log_level="warning", access_log=False)
        finally:
            app.state.sessions.kw["bind"].dispose()


if __name__ == "__main__":
    main()
