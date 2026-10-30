"""Owner-selected Teams chats with confidential OAuth/PKCE. No external writes."""

import base64
import hashlib
import math
import secrets
import time
from typing import Annotated
from urllib.parse import quote, urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from ghosttab_api import calendar, google_sources
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.connector_adapters import (
    BoundedRead,
    ConnectorFailure,
    identifier,
    read_selected,
    request,
)
from ghosttab_api.models import Evidence, SourceConnection, SourceOAuthState, SourceReference
from ghosttab_api.workspaces import owned_task, put_evidence

router = APIRouter(prefix="/api")
User = Annotated[Principal, Depends(current_user)]
SCOPE = "https://graph.microsoft.com/Chat.Read"


def tenant(settings):
    try:
        return str(UUID(settings.teams_tenant_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            503, "Teams needs a work/school tenant ID; see docs/teams-source.md"
        ) from exc


def configured(settings):
    try:
        tenant(settings)
    except HTTPException:
        return False
    return bool(
        settings.teams_client_id
        and settings.teams_client_secret.get_secret_value()
        and settings.token_encryption_key.get_secret_value()
    )


def begin(factory, settings, owner):
    if not configured(settings):
        raise HTTPException(503, "Teams needs server configuration; see docs/teams-source.md")
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    digest = hashlib.sha256(state.encode()).hexdigest()
    with factory.begin() as session:
        if session.get(SourceConnection, (owner, "teams")):
            raise HTTPException(409, "Disconnect Teams before connecting another account")
        session.execute(
            delete(SourceOAuthState).where(
                SourceOAuthState.owner_id == owner, SourceOAuthState.provider == "teams"
            )
        )
        session.add(
            SourceOAuthState(
                digest=digest,
                owner_id=owner,
                provider="teams",
                encrypted_verifier=calendar.encrypt(
                    settings, {"verifier": verifier, "tenant": tenant(settings)}
                ),
                expires_at=time.time() + 600,
            )
        )
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    return (
        f"https://login.microsoftonline.com/{tenant(settings)}/oauth2/v2.0/authorize?"
        + urlencode(
            {
                "client_id": settings.teams_client_id,
                "response_type": "code",
                "response_mode": "query",
                "redirect_uri": settings.teams_redirect_uri,
                "scope": SCOPE + " offline_access",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        ),
        digest,
    )


def exchange(settings, data):
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post(
                f"https://login.microsoftonline.com/{tenant(settings)}/oauth2/v2.0/token",
                data={
                    "client_id": settings.teams_client_id,
                    "client_secret": settings.teams_client_secret.get_secret_value(),
                    "scope": SCOPE + " offline_access",
                    **data,
                },
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise HTTPException(503, "Microsoft authorization is temporarily unavailable")
        body = response.json()
        if not response.is_success:
            if body.get("error") == "invalid_grant":
                raise HTTPException(401, "Teams authorization expired or was revoked; reconnect")
            raise HTTPException(502, "Teams authorization could not finish; check server setup")
        if (
            not isinstance(body.get("access_token"), str)
            or not body["access_token"]
            or type(body.get("expires_in")) is not int
            or body["expires_in"] <= 0
            or str(body.get("token_type", "")).lower() != "bearer"
            or not isinstance(body.get("refresh_token", ""), str)
            or not isinstance(body.get("scope", ""), str)
        ):
            raise ValueError("Incomplete grant")
        return {
            "access_token": body["access_token"],
            "refresh_token": body.get("refresh_token", ""),
            "expires_at": time.time() + body["expires_in"],
            "scope": body.get("scope", ""),
            "tenant_id": tenant(settings),
        }
    except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError) as exc:
        raise HTTPException(
            502, "Microsoft returned incomplete authorization; retry later"
        ) from exc


def readable(scope):
    return isinstance(scope, str) and any(x in ("Chat.Read", SCOPE) for x in scope.split())


def valid_tokens(tokens):
    return (
        isinstance(tokens, dict)
        and all(
            isinstance(tokens.get(key), str) and tokens[key]
            for key in ("access_token", "refresh_token", "tenant_id")
        )
        and type(tokens.get("expires_at")) in (int, float)
        and math.isfinite(tokens["expires_at"])
        and readable(tokens.get("scope"))
    )


def finish(factory, settings, state, cookie, code, error):
    digest = hashlib.sha256(state.encode()).hexdigest()
    if not cookie or not secrets.compare_digest(cookie, digest):
        raise HTTPException(400, "Finish Teams authorization in the browser where it started")
    with factory.begin() as session:
        pending = session.execute(
            delete(SourceOAuthState)
            .where(
                SourceOAuthState.digest == digest,
                SourceOAuthState.provider == "teams",
                SourceOAuthState.expires_at > time.time(),
            )
            .returning(SourceOAuthState.owner_id, SourceOAuthState.encrypted_verifier)
        ).first()
    if not pending or error or not code:
        raise HTTPException(400, "Teams consent expired, was declined or was already used")
    saved = calendar.decrypt(settings, pending.encrypted_verifier)
    if saved["tenant"] != tenant(settings):
        raise HTTPException(409, "Teams tenant changed; start authorization again")
    tokens = exchange(
        settings,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.teams_redirect_uri,
            "code_verifier": saved["verifier"],
        },
    )
    if not readable(tokens["scope"]) or not tokens["refresh_token"]:
        raise HTTPException(400, "Teams chat read permission and offline access are required")
    with factory.begin() as session:
        if session.get(SourceConnection, (pending.owner_id, "teams")):
            raise HTTPException(409, "Teams is already connected")
        session.add(
            SourceConnection(
                owner_id=pending.owner_id,
                provider="teams",
                encrypted_tokens=calendar.encrypt(settings, tokens),
            )
        )


def access(factory, settings, owner):
    grant_id = None
    try:
        with factory.begin() as session:
            row = google_sources.grant(session, owner, "teams", lock=True)
            grant_id = row.grant_id
            tokens = calendar.decrypt(settings, row.encrypted_tokens)
            if not valid_tokens(tokens):
                raise HTTPException(401, "Teams credentials are incomplete; reconnect")
            if tokens["tenant_id"] != tenant(settings):
                raise HTTPException(401, "Teams tenant changed; reconnect")
            if tokens["expires_at"] <= time.time() + 60:
                fresh = exchange(
                    settings,
                    {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
                )
                fresh["refresh_token"] = fresh["refresh_token"] or tokens["refresh_token"]
                fresh["scope"] = fresh["scope"] or tokens["scope"]
                tokens = fresh
                row.encrypted_tokens = calendar.encrypt(settings, tokens)
            if not readable(tokens["scope"]):
                raise HTTPException(401, "Teams chat read access is missing; reconnect")
        return tokens, grant_id
    except HTTPException as exc:
        if exc.status_code == 401 and grant_id:
            google_sources.disconnect(factory, owner, "teams", expected=grant_id)
        raise


def client_for(token):
    return httpx.Client(
        headers={"Authorization": "Bearer " + token}, timeout=20, follow_redirects=False
    )


def read_chat(tokens, chat_id):
    identifier(chat_id, r"19:[A-Za-z0-9_.@-]+")
    with client_for(tokens["access_token"]) as client:
        reader = BoundedRead(client)
        metadata = request(
            reader, "https://graph.microsoft.com/v1.0/me/chats/" + quote(chat_id, safe="")
        )
        if metadata.get("id") != chat_id or metadata.get("chatType") not in (
            "oneOnOne",
            "group",
            "meeting",
        ):
            raise ConnectorFailure("invalid_response")
        source = read_selected(reader, "teams", chat_id)
        title = metadata.get("topic") or "Selected Teams chat"
        if not isinstance(title, str):
            raise ConnectorFailure("invalid_response")
        return source.evidence.model_copy(update={"title": title[:240]})


def failure(factory, owner, grant_id, exc):
    if exc.code == "connection_revoked":
        google_sources.disconnect(factory, owner, "teams", expected=grant_id)
        return HTTPException(401, "Teams access was revoked; reconnect")
    if exc.retryable:
        return HTTPException(503, "Teams is unavailable or rate limited; retry later")
    if exc.code == "source_empty":
        return HTTPException(422, "This chat excerpt contains no readable message text")
    return HTTPException(
        403 if exc.code in ("access_denied", "source_unavailable") else 502,
        "Teams could not provide this chat; check your access and selection",
    )


@router.get("/integrations/teams")
def status(req: Request, user: User):
    with req.app.state.sessions() as session:
        return {
            "connected": session.get(SourceConnection, (user.id, "teams")) is not None,
            "configured": configured(req.app.state.settings),
        }


@router.post("/integrations/teams/start")
def start(req: Request, user: User):
    settings = req.app.state.settings
    url, digest = begin(req.app.state.sessions, settings, user.id)
    response = JSONResponse({"url": url})
    response.set_cookie(
        "ghosttab_teams_oauth",
        digest,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=600,
        path="/api/integrations/teams/callback",
    )
    return response


@router.get("/integrations/teams/callback")
def callback(
    req: Request,
    state: Annotated[str, Query(max_length=200)] = "",
    code: Annotated[str, Query(max_length=4096)] = "",
    error: Annotated[str, Query(max_length=200)] = "",
):
    outcome = "connected"
    try:
        finish(
            req.app.state.sessions,
            req.app.state.settings,
            state,
            req.cookies.get("ghosttab_teams_oauth"),
            code,
            error,
        )
    except HTTPException:
        outcome = "connection_failed"
    response = RedirectResponse(
        req.app.state.settings.frontend_url + "?source=teams&result=" + outcome, status_code=303
    )
    response.delete_cookie("ghosttab_teams_oauth", path="/api/integrations/teams/callback")
    return response


@router.delete("/integrations/teams", status_code=204)
def disconnect(req: Request, user: User):
    google_sources.disconnect(req.app.state.sessions, user.id, "teams")


class ChatSelection(BaseModel):
    chat_id: str = Field(pattern=r"^19:[A-Za-z0-9_.@-]+$", max_length=256)


@router.post("/tasks/{task_id}/imports/teams")
def import_chat(task_id: str, body: ChatSelection, req: Request, user: User):
    factory, settings = req.app.state.sessions, req.app.state.settings
    with factory() as session:
        owned_task(session, task_id, user.id)
    tokens, grant_id = access(factory, settings, user.id)
    try:
        source = read_chat(tokens, body.chat_id)
    except ConnectorFailure as exc:
        raise failure(factory, user.id, grant_id, exc) from exc
    with factory.begin() as session:
        google_sources.grant(session, user.id, "teams", grant_id, lock=True)
        task = owned_task(session, task_id, user.id, lock=True)
        external = body.chat_id
        item = session.scalar(
            select(Evidence)
            .join(SourceReference, SourceReference.evidence_id == Evidence.id)
            .where(
                Evidence.task_id == task_id,
                Evidence.removed.is_(False),
                SourceReference.provider == "teams",
                SourceReference.grant_id == grant_id,
                SourceReference.external_id == external,
            )
        )
        imported = put_evidence(session, task, source, item=item, origin="teams")
        if item is None:
            session.add(
                SourceReference(
                    evidence_id=imported.id,
                    provider="teams",
                    external_id=external,
                    grant_id=grant_id,
                )
            )
        return {"id": imported.id}


def refresh_chat(factory, settings, owner, task_id, evidence_id):
    with factory() as session:
        owned_task(session, task_id, owner)
        item = session.get(Evidence, evidence_id)
        ref = session.get(SourceReference, evidence_id)
        if (
            not item
            or item.task_id != task_id
            or item.removed
            or not ref
            or ref.provider != "teams"
        ):
            raise HTTPException(404, "Teams source not found")
        external, expected = ref.external_id, ref.grant_id
    tokens, grant_id = access(factory, settings, owner)
    if grant_id != expected:
        raise HTTPException(409, "Teams connection changed; remove and import this source again")
    missing = False
    try:
        source = read_chat(tokens, external)
    except ConnectorFailure as exc:
        if exc.code in ("access_denied", "source_unavailable", "source_empty"):
            missing = True
        else:
            raise failure(factory, owner, grant_id, exc) from exc
    with factory.begin() as session:
        google_sources.grant(session, owner, "teams", grant_id, lock=True)
        task = owned_task(session, task_id, owner, lock=True)
        item = session.get(Evidence, evidence_id, populate_existing=True)
        ref = session.get(SourceReference, evidence_id, populate_existing=True)
        if not item or item.removed or not ref or ref.grant_id != grant_id:
            raise HTTPException(409, "Source was removed; reload this workspace")
        if missing:
            item.removed = True
            task.generation += 1
        else:
            put_evidence(session, task, source, item=item)
    return {"removed": missing}
