"""Owner-scoped, explicit Google Docs/Gmail imports. No automatic discovery or AI."""

import base64
import hashlib
import secrets
import time
from typing import Annotated, Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update

from ghosttab_api import calendar
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.connector_adapters import ConnectorFailure, identifier, read_selected, request
from ghosttab_api.models import Evidence, SourceConnection, SourceOAuthState, SourceReference, Task
from ghosttab_api.workspaces import owned_task, put_evidence

Provider = Literal["google_docs", "gmail"]
User = Annotated[Principal, Depends(current_user)]
SCOPES = {
    "google_docs": "https://www.googleapis.com/auth/documents.readonly",
    "gmail": "https://www.googleapis.com/auth/gmail.readonly",
}
router = APIRouter(prefix="/api")


def callback_url(settings, provider):
    return settings.google_sources_callback_base.rstrip("/") + f"/{provider}/callback"


def grant(session, owner, provider, expected=None, *, lock=False):
    if lock:
        session.execute(
            update(SourceConnection)
            .where(SourceConnection.owner_id == owner, SourceConnection.provider == provider)
            .values(grant_id=SourceConnection.grant_id)
        )
    row = session.get(SourceConnection, (owner, provider), populate_existing=True)
    if not row or (expected is not None and row.grant_id != expected):
        raise HTTPException(409, "Source connection changed; reconnect or reload and try again")
    return row


def disconnect(factory, owner, provider, *, expected=None):
    with factory.begin() as session:
        # Lock connection before tasks: imports and refreshes use the same order.
        session.execute(
            update(SourceConnection)
            .where(SourceConnection.owner_id == owner, SourceConnection.provider == provider)
            .values(grant_id=SourceConnection.grant_id)
        )
        current = session.get(SourceConnection, (owner, provider), populate_existing=True)
        if expected is not None and (not current or current.grant_id != expected):
            return
        for task in session.scalars(select(Task).where(Task.owner_id == owner).with_for_update()):
            rows = session.scalars(
                select(Evidence).where(
                    Evidence.task_id == task.id,
                    Evidence.origin == provider,
                    Evidence.removed.is_(False),
                )
            ).all()
            if rows:
                for row in rows:
                    row.removed = True
                task.generation += 1
        session.execute(
            delete(SourceConnection).where(
                SourceConnection.owner_id == owner, SourceConnection.provider == provider
            )
        )
        session.execute(
            delete(SourceOAuthState).where(
                SourceOAuthState.owner_id == owner, SourceOAuthState.provider == provider
            )
        )


def begin(factory, settings, owner, provider):
    if not settings.google_ready:
        raise HTTPException(
            503, "Google authorization needs server configuration; see docs/setup.md"
        )
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    digest = hashlib.sha256(state.encode()).hexdigest()
    with factory.begin() as session:
        if session.get(SourceConnection, (owner, provider)):
            raise HTTPException(409, "Disconnect this source before connecting another account")
        session.execute(
            delete(SourceOAuthState).where(
                SourceOAuthState.owner_id == owner, SourceOAuthState.provider == provider
            )
        )
        session.add(
            SourceOAuthState(
                digest=digest,
                owner_id=owner,
                provider=provider,
                encrypted_verifier=calendar.encrypt(settings, verifier),
                expires_at=time.time() + 600,
            )
        )
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": callback_url(settings, provider),
            "response_type": "code",
            "scope": SCOPES[provider],
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "code_challenge": challenge.decode(),
            "code_challenge_method": "S256",
        }
    ), digest


def finish(factory, settings, provider, state, cookie, code, error):
    digest = hashlib.sha256(state.encode()).hexdigest()
    if not cookie or not secrets.compare_digest(digest, cookie):
        raise HTTPException(400, "Finish authorization in the browser where it started")
    with factory.begin() as session:
        pending = session.execute(
            delete(SourceOAuthState)
            .where(
                SourceOAuthState.digest == digest,
                SourceOAuthState.provider == provider,
                SourceOAuthState.expires_at > time.time(),
            )
            .returning(SourceOAuthState.owner_id, SourceOAuthState.encrypted_verifier)
        ).first()
    if not pending or error or not code:
        raise HTTPException(400, "Authorization expired, was declined, or was already used")
    tokens = calendar.token_exchange(
        settings,
        {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": callback_url(settings, provider),
            "code_verifier": calendar.decrypt(settings, pending.encrypted_verifier),
        },
    )
    if SCOPES[provider] not in tokens["scope"].split() or not tokens["refresh_token"]:
        raise HTTPException(400, "Read-only access and offline authorization are required")
    with factory.begin() as session:
        if session.get(SourceConnection, (pending.owner_id, provider)):
            raise HTTPException(409, "This source is already connected")
        session.add(
            SourceConnection(
                owner_id=pending.owner_id,
                provider=provider,
                encrypted_tokens=calendar.encrypt(settings, tokens),
            )
        )


def access(factory, settings, owner, provider):
    with factory() as session:
        row = grant(session, owner, provider)
        encrypted, grant_id = row.encrypted_tokens, row.grant_id
    tokens = calendar.decrypt(settings, encrypted)
    if tokens["expires_at"] <= time.time() + 60:
        try:
            fresh = calendar.token_exchange(
                settings, {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
            )
        except HTTPException as exc:
            if exc.status_code == 401:
                disconnect(factory, owner, provider, expected=grant_id)
            raise
        fresh["refresh_token"] = fresh["refresh_token"] or tokens["refresh_token"]
        fresh["scope"] = fresh["scope"] or tokens["scope"]
        tokens = fresh
        with factory.begin() as session:
            changed = session.execute(
                update(SourceConnection)
                .where(
                    SourceConnection.owner_id == owner,
                    SourceConnection.provider == provider,
                    SourceConnection.grant_id == grant_id,
                    SourceConnection.encrypted_tokens == encrypted,
                )
                .values(encrypted_tokens=calendar.encrypt(settings, tokens))
            ).rowcount
            if not changed:
                raise HTTPException(409, "Connection changed; try again")
    if SCOPES[provider] not in tokens["scope"].split():
        disconnect(factory, owner, provider, expected=grant_id)
        raise HTTPException(401, "Required source permission is missing; reconnect")
    return tokens["access_token"], grant_id


def client_for(token):
    return httpx.Client(
        headers={"Authorization": f"Bearer {token}"}, timeout=20, follow_redirects=False
    )


def failure(exc):
    messages = {
        "access_denied": (403, "Google denied access. Check permissions or reconnect this source."),
        "source_unavailable": (404, "This source is no longer available to this account."),
        "invalid_selection": (422, "Choose a valid Google document ID or Gmail message ID."),
    }
    status, message = messages.get(
        exc.code,
        (503 if exc.retryable else 502, "Google could not return this source; try again later."),
    )
    return HTTPException(status, message)


@router.get("/integrations/google/{provider}")
def connection_status(provider: Provider, req: Request, user: User):
    with req.app.state.sessions() as session:
        return {
            "connected": session.get(SourceConnection, (user.id, provider)) is not None,
            "configured": req.app.state.settings.google_ready,
        }


@router.post("/integrations/google/{provider}/start")
def start(provider: Provider, req: Request, user: User):
    settings = req.app.state.settings
    url, digest = begin(req.app.state.sessions, settings, user.id, provider)
    response = JSONResponse({"url": url})
    response.set_cookie(
        f"ghosttab_{provider}_oauth",
        digest,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=600,
        path=f"/api/integrations/google/{provider}/callback",
    )
    return response


@router.get("/integrations/google/{provider}/callback")
def callback(
    provider: Provider,
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
            provider,
            state,
            req.cookies.get(f"ghosttab_{provider}_oauth"),
            code,
            error,
        )
    except HTTPException:
        outcome = "connection_failed"
    response = RedirectResponse(
        req.app.state.settings.frontend_url + f"?source={provider}&result={outcome}",
        status_code=303,
    )
    response.delete_cookie(
        f"ghosttab_{provider}_oauth", path=f"/api/integrations/google/{provider}/callback"
    )
    return response


@router.delete("/integrations/google/{provider}", status_code=204)
def remove_connection(provider: Provider, req: Request, user: User):
    disconnect(req.app.state.sessions, user.id, provider)


@router.get("/integrations/gmail/messages")
def messages(req: Request, user: User, q: Annotated[str, Query(min_length=1, max_length=200)]):
    token, grant_id = access(req.app.state.sessions, req.app.state.settings, user.id, "gmail")
    try:
        deadline = time.monotonic() + 20
        with client_for(token) as client:
            data = request(
                client,
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                q=q,
                maxResults=5,
                includeSpamTrash="false",
            )
            items = []
            for item in data.get("messages", [])[:5]:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ConnectorFailure("provider_unavailable", retryable=True)
                item_id = identifier(item.get("id"), r"[a-fA-F0-9]+")
                metadata = request(
                    client,
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item_id}",
                    format="metadata",
                    metadataHeaders="Subject",
                    request_timeout=remaining,
                )
                headers = metadata.get("payload", {}).get("headers", [])
                title = next(
                    (x.get("value", "") for x in headers if x.get("name", "").lower() == "subject"),
                    "Email message",
                )
                items.append({"id": item_id, "title": title[:200] or "Email message"})
        with req.app.state.sessions() as session:
            grant(session, user.id, "gmail", grant_id)
        return {"messages": items, "has_more": bool(data.get("nextPageToken"))}
    except ConnectorFailure as exc:
        raise failure(exc) from exc
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise HTTPException(
            502, "Google returned an unreadable message list; try again later"
        ) from exc


class Selection(BaseModel):
    item_id: str = Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("/tasks/{task_id}/imports/{provider}")
def import_source(task_id: str, provider: Provider, body: Selection, req: Request, user: User):
    factory, settings = req.app.state.sessions, req.app.state.settings
    with factory() as session:
        owned_task(session, task_id, user.id)
    token, grant_id = access(factory, settings, user.id, provider)
    try:
        with client_for(token) as client:
            source = read_selected(client, provider, body.item_id)
    except ConnectorFailure as exc:
        raise failure(exc) from exc
    with factory.begin() as session:
        grant(session, user.id, provider, grant_id, lock=True)
        task = owned_task(session, task_id, user.id, lock=True)
        item = session.scalar(
            select(Evidence)
            .join(SourceReference, SourceReference.evidence_id == Evidence.id)
            .where(
                Evidence.task_id == task.id,
                Evidence.removed.is_(False),
                SourceReference.provider == provider,
                SourceReference.external_id == body.item_id,
                SourceReference.grant_id == grant_id,
            )
        )
        imported = put_evidence(session, task, source.evidence, item=item, origin=provider)
        if item is None:
            session.add(
                SourceReference(
                    evidence_id=imported.id,
                    provider=provider,
                    external_id=body.item_id,
                    grant_id=grant_id,
                )
            )
        return {"id": imported.id}


@router.post("/tasks/{task_id}/evidence/{evidence_id}/refresh")
def refresh_source(task_id: str, evidence_id: str, req: Request, user: User):
    factory, settings = req.app.state.sessions, req.app.state.settings
    with factory() as session:
        owned_task(session, task_id, user.id)
        item = session.get(Evidence, evidence_id)
        ref = session.get(SourceReference, evidence_id)
        if not item or item.task_id != task_id or item.removed or not ref:
            raise HTTPException(404, "Connected source not found")
        provider, external_id, expected = ref.provider, ref.external_id, ref.grant_id
    if provider == "slack":
        from ghosttab_api.slack_sources import refresh_thread

        return refresh_thread(factory, settings, user.id, task_id, evidence_id)
    if provider == "teams":
        from ghosttab_api.teams_sources import refresh_chat

        return refresh_chat(factory, settings, user.id, task_id, evidence_id)
    if provider == "jira":
        from ghosttab_api.jira_sources import refresh_issue

        return refresh_issue(factory, settings, user.id, task_id, evidence_id)
    token, grant_id = access(factory, settings, user.id, provider)
    if grant_id != expected:
        raise HTTPException(409, "Source belongs to an earlier connection; remove and import again")
    missing = False
    try:
        with client_for(token) as client:
            source = read_selected(client, provider, external_id)
    except ConnectorFailure as exc:
        if exc.code in ("source_unavailable", "access_denied"):
            missing = True
        else:
            raise failure(exc) from exc
    with factory.begin() as session:
        grant(session, user.id, provider, grant_id, lock=True)
        task = owned_task(session, task_id, user.id, lock=True)
        item = session.get(Evidence, evidence_id, populate_existing=True)
        if item.removed:
            raise HTTPException(409, "Source was removed while checking; reload this workspace")
        if missing:
            item.removed = True
            task.generation += 1
        else:
            put_evidence(session, task, source.evidence, item=item)
    return {"removed": missing}
