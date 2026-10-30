"""Disposable auth UI rehearsal at 8011. No real Supabase, email or model calls.

Fictional sign-in: demo@example.test / demo-password. Production JWT verification
is NOT changed; this fixture alone supplies a local synthetic token verifier.
"""

import html
import secrets
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import jwt
import uvicorn
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from ghosttab_api.auth import Principal, current_user
from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.main import create_app
from ghosttab_api.models import Base, Budget


def main():
    with TemporaryDirectory(prefix="ghosttab-auth-qa-") as folder:
        # HTTP is allowed only in this isolated fixture. Real settings require HTTPS.
        settings = Settings(
            _env_file=None,
            environment="test",
            synthetic_demo=True,
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
        secret = secrets.token_hex(32)
        profile = {
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

        def token():
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
            if request.query_params.get("grant_type") != "refresh_token" and (
                body.get("email") != "demo@example.test" or body.get("password") != "demo-password"
            ):
                return JSONResponse({"msg": "Invalid fictional credentials"}, status_code=400)
            return {
                "access_token": token(),
                "refresh_token": "synthetic-refresh",
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
                + "&refresh_token=synthetic-refresh&type=signup&expires_in=3600&token_type=bearer",
                status_code=303,
            )

        @app.post("/auth/v1/signup")
        async def signup(request: Request):
            body = await request.json()
            profile["user_metadata"] = {
                "full_name": str(body.get("data", {}).get("full_name", "Fictional User"))[:80]
            }
            return {**profile, "confirmation_sent_at": "2026-10-29T00:00:00Z"}

        @app.post("/auth/v1/recover")
        @app.post("/auth/v1/resend")
        def email_request():
            return {}

        @app.get("/auth/v1/user")
        @app.put("/auth/v1/user")
        def user(request: Request):
            synthetic_user(request)
            return profile

        @app.post("/auth/v1/logout")
        def logout():
            return Response(status_code=204)

        @app.get("/synthetic-recovery")
        def recovery():
            url = (
                "http://127.0.0.1:8011/?auth=recovery#access_token="
                + token()
                + "&refresh_token=synthetic-refresh&type=recovery&expires_in=3600&token_type=bearer"
            )
            return HTMLResponse(
                '<p>Synthetic recovery only. No email was sent.</p><a href="'
                + html.escape(url)
                + '">Open synthetic recovery link</a>'
            )

        dist = Path(__file__).resolve().parents[3] / "apps/web/dist"
        app.mount("/", StaticFiles(directory=dist, html=True))
        try:
            uvicorn.run(app, host="127.0.0.1", port=8011, log_level="warning", access_log=False)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
