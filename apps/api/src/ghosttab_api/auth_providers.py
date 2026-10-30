"""Public provider availability; never accepts credentials from the browser."""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Request

router = APIRouter(prefix="/api")


def provider_status(req: Request):
    settings = req.app.state.settings
    if settings.auth_mode != "supabase":
        return {"google": "disabled"}
    try:
        with httpx.Client(timeout=3, follow_redirects=False) as client:
            response = client.get(
                settings.supabase_url.rstrip("/") + "/auth/v1/settings",
                headers={"apikey": settings.supabase_publishable_key},
            )
        if not response.is_success or len(response.content) > 65_536:
            return {"google": "unavailable"}
        value = response.json().get("external", {}).get("google")
        if type(value) is not bool:
            return {"google": "unavailable"}
        return {"google": "enabled" if value else "disabled"}
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return {"google": "unavailable"}


@router.get("/auth/providers")
def providers(status: Annotated[dict, Depends(provider_status)]):
    return status
