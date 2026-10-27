from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Request

from ghosttab_api.config import Settings


@dataclass(frozen=True)
class Principal:
    id: str


def current_user(request: Request) -> Principal:
    settings: Settings = request.app.state.settings
    if settings.auth_mode == "local":
        # The custom header, loopback binding, host and origin checks together
        # restrict this development-only identity to local application requests.
        if (
            not request.client
            or request.client.host not in ("127.0.0.1", "::1", "testclient")
            or request.headers.get("x-ghosttab-local") != "1"
            or request.headers.get("origin", settings.frontend_url)
            not in (settings.frontend_url, "http://127.0.0.1:8000")
        ):
            raise HTTPException(401, "Local workspace access requires this computer")
        return Principal("local-owner")
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(401, "Sign in to continue")
    token = header[7:]
    try:
        key = request.app.state.jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=["ES256", "RS256"],
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
            audience="authenticated",
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
        if claims.get("role") != "authenticated" or not claims["sub"]:
            raise jwt.InvalidTokenError()
        return Principal(claims["sub"])
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Your session is invalid or expired; sign in again") from exc
