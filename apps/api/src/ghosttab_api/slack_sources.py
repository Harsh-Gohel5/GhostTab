"""Explicit public-channel thread imports using a confidential web OAuth client."""

import hashlib
import secrets
import time
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from ghosttab_api import calendar, google_sources
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.connector_adapters import ConnectorFailure, identifier, read_selected, request
from ghosttab_api.models import Evidence, SourceConnection, SourceOAuthState, SourceReference
from ghosttab_api.workspaces import owned_task, put_evidence

router = APIRouter(prefix="/api")
User = Annotated[Principal, Depends(current_user)]
SCOPES = {"channels:read", "channels:history"}


def configured(settings):
    return bool(
        settings.slack_client_id
        and settings.slack_client_secret.get_secret_value()
        and settings.token_encryption_key.get_secret_value()
    )


def begin(factory, settings, owner):
    if not configured(settings):
        raise HTTPException(503, "Slack needs server configuration; see docs/slack-source.md")
    state = secrets.token_urlsafe(32)
    digest = hashlib.sha256(state.encode()).hexdigest()
    with factory.begin() as session:
        if session.get(SourceConnection, (owner, "slack")):
            raise HTTPException(409, "Disconnect Slack before connecting another workspace")
        session.execute(
            delete(SourceOAuthState).where(
                SourceOAuthState.owner_id == owner, SourceOAuthState.provider == "slack"
            )
        )
        session.add(
            SourceOAuthState(
                digest=digest,
                owner_id=owner,
                provider="slack",
                encrypted_verifier=calendar.encrypt(settings, "confidential-web-client"),
                expires_at=time.time() + 600,
            )
        )
    return "https://slack.com/oauth/v2/authorize?" + urlencode(
        {
            "client_id": settings.slack_client_id,
            "user_scope": ",".join(sorted(SCOPES)),
            "redirect_uri": settings.slack_redirect_uri,
            "state": state,
        }
    ), digest


def exchange(settings, data, *, refresh=False):
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": settings.slack_client_id,
                    "client_secret": settings.slack_client_secret.get_secret_value(),
                    **data,
                },
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise HTTPException(503, "Slack authorization is temporarily unavailable")
        body = response.json()
        if not response.is_success or body.get("ok") is not True:
            raise HTTPException(401, "Slack authorization expired or was declined; reconnect")
        user = body if refresh else body.get("authed_user", {})
        if (
            user.get("token_type") != "user"
            or not isinstance(user.get("access_token"), str)
            or not user.get("access_token")
        ):
            raise HTTPException(400, "Slack user read access is required")
        scopes = user.get("scope", "")
        if not SCOPES <= set(scopes.split(",")):
            raise HTTPException(400, "Slack public-channel read permissions are required")
        expires = user.get("expires_in")
        if refresh and (expires is None or not user.get("refresh_token")):
            raise HTTPException(502, "Slack returned incomplete rotating credentials")
        if expires is not None and (
            not isinstance(expires, int) or expires <= 0 or not user.get("refresh_token")
        ):
            raise HTTPException(502, "Slack returned incomplete rotating credentials")
        return {
            "access_token": user["access_token"],
            "refresh_token": user.get("refresh_token", ""),
            "scope": scopes,
            "expires_at": time.time() + expires if expires else None,
            "team_id": body.get("team", {}).get("id", ""),
        }
    except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(502, "Slack authorization could not finish; try again later") from exc


def finish(factory, settings, state, cookie, code, error):
    digest = hashlib.sha256(state.encode()).hexdigest()
    if not cookie or not secrets.compare_digest(cookie, digest):
        raise HTTPException(400, "Finish Slack authorization in the browser where it started")
    with factory.begin() as session:
        pending = session.execute(
            delete(SourceOAuthState)
            .where(
                SourceOAuthState.digest == digest,
                SourceOAuthState.provider == "slack",
                SourceOAuthState.expires_at > time.time(),
            )
            .returning(SourceOAuthState.owner_id)
        ).first()
    if not pending or error or not code:
        raise HTTPException(400, "Slack authorization expired, was declined or was already used")
    tokens = exchange(settings, {"code": code, "redirect_uri": settings.slack_redirect_uri})
    try:
        identifier(tokens["team_id"], r"T[A-Z0-9]+")
    except ConnectorFailure as exc:
        raise HTTPException(502, "Slack workspace identity is missing") from exc
    with factory.begin() as session:
        if session.get(SourceConnection, (pending.owner_id, "slack")):
            raise HTTPException(409, "Slack is already connected")
        session.add(
            SourceConnection(
                owner_id=pending.owner_id,
                provider="slack",
                encrypted_tokens=calendar.encrypt(settings, tokens),
            )
        )


def access(factory, settings, owner):
    grant_id = None
    try:
        with factory.begin() as session:
            # Serialize rotating single-use refresh tokens; re-read after obtaining the lock.
            row = google_sources.grant(session, owner, "slack", lock=True)
            grant_id = row.grant_id
            tokens = calendar.decrypt(settings, row.encrypted_tokens)
            if tokens["expires_at"] is not None and tokens["expires_at"] <= time.time() + 60:
                fresh = exchange(
                    settings,
                    {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
                    refresh=True,
                )
                if fresh["team_id"] and fresh["team_id"] != tokens["team_id"]:
                    raise HTTPException(401, "Slack workspace identity changed; reconnect")
                fresh["team_id"] = tokens["team_id"]
                tokens = fresh
                row.encrypted_tokens = calendar.encrypt(settings, tokens)
            if not SCOPES <= set(tokens["scope"].split(",")):
                raise HTTPException(401, "Slack read permissions are missing; reconnect")
        return tokens, grant_id
    except HTTPException as exc:
        if exc.status_code == 401 and grant_id:
            google_sources.disconnect(factory, owner, "slack", expected=grant_id)
        raise


def client_for(token):
    return httpx.Client(
        headers={"Authorization": "Bearer " + token}, timeout=20, follow_redirects=False
    )


class BoundedRead:
    def __init__(self, client):
        self.client = client
        self.deadline = time.monotonic() + 20

    def get(self, url, **kwargs):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise httpx.TimeoutException("Source read deadline reached")
        kwargs["timeout"] = min(remaining, kwargs.get("timeout", 20))
        return self.client.get(url, **kwargs)


def read_thread(tokens, channel, timestamp):
    try:
        return _read_thread(tokens, channel, timestamp)
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise ConnectorFailure("invalid_response") from exc


def _read_thread(tokens, channel, timestamp):
    with client_for(tokens["access_token"]) as client:
        reader = BoundedRead(client)
        info = request(reader, "https://slack.com/api/conversations.info", channel=channel)
        if info.get("ok") is not True:
            code = info.get("error")
            if code in ("invalid_auth", "token_revoked", "account_inactive", "not_authed"):
                raise ConnectorFailure("connection_revoked")
            if code == "ratelimited":
                raise ConnectorFailure("provider_unavailable", retryable=True)
            raise ConnectorFailure("access_denied")
        metadata = info.get("channel", {})
        if (
            metadata.get("id") != channel
            or metadata.get("is_private") is not False
            or metadata.get("is_im")
            or metadata.get("is_mpim")
        ):
            raise ConnectorFailure("access_denied")
        source = read_selected(reader, "slack", timestamp, container_id=channel)
    return source.evidence.model_copy(
        update={
            "title": ("Slack #" + str(metadata.get("name") or channel) + " thread")[:200],
            "url": "https://slack.com/app_redirect?"
            + urlencode({"team": tokens["team_id"], "channel": channel}),
        }
    )


def failure(factory, owner, grant_id, exc):
    if exc.code == "connection_revoked":
        google_sources.disconnect(factory, owner, "slack", expected=grant_id)
        return HTTPException(401, "Slack access was revoked; reconnect")
    if exc.retryable:
        return HTTPException(503, "Slack is temporarily unavailable or rate limited; try later")
    if exc.code in ("access_denied", "source_unavailable"):
        return HTTPException(
            403, "This public Slack thread is unavailable to the connected account"
        )
    return HTTPException(502, "Slack could not return this thread; check the selection and retry")


@router.get("/integrations/slack")
def status(req: Request, user: User):
    with req.app.state.sessions() as session:
        return {
            "connected": session.get(SourceConnection, (user.id, "slack")) is not None,
            "configured": configured(req.app.state.settings),
        }


@router.post("/integrations/slack/start")
def start(req: Request, user: User):
    settings = req.app.state.settings
    url, digest = begin(req.app.state.sessions, settings, user.id)
    response = JSONResponse({"url": url})
    response.set_cookie(
        "ghosttab_slack_oauth",
        digest,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=600,
        path="/api/integrations/slack/callback",
    )
    return response


@router.get("/integrations/slack/callback")
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
            req.cookies.get("ghosttab_slack_oauth"),
            code,
            error,
        )
    except HTTPException:
        outcome = "connection_failed"
    response = RedirectResponse(
        req.app.state.settings.frontend_url + "?source=slack&result=" + outcome, status_code=303
    )
    response.delete_cookie("ghosttab_slack_oauth", path="/api/integrations/slack/callback")
    return response


@router.delete("/integrations/slack", status_code=204)
def disconnect(req: Request, user: User):
    google_sources.disconnect(req.app.state.sessions, user.id, "slack")


class ThreadSelection(BaseModel):
    channel_id: str = Field(pattern=r"^C[A-Z0-9]{1,60}$")
    thread_ts: str = Field(pattern=r"^[0-9]{10,16}\.[0-9]{6}$")


@router.post("/tasks/{task_id}/imports/slack")
def import_thread(task_id: str, body: ThreadSelection, req: Request, user: User):
    factory, settings = req.app.state.sessions, req.app.state.settings
    with factory() as session:
        owned_task(session, task_id, user.id)
    tokens, grant_id = access(factory, settings, user.id)
    try:
        source = read_thread(tokens, body.channel_id, body.thread_ts)
    except ConnectorFailure as exc:
        raise failure(factory, user.id, grant_id, exc) from exc
    with factory.begin() as session:
        google_sources.grant(session, user.id, "slack", grant_id, lock=True)
        task = owned_task(session, task_id, user.id, lock=True)
        external = body.channel_id + "|" + body.thread_ts
        item = session.scalar(
            select(Evidence)
            .join(SourceReference, SourceReference.evidence_id == Evidence.id)
            .where(
                Evidence.task_id == task_id,
                Evidence.removed.is_(False),
                SourceReference.provider == "slack",
                SourceReference.grant_id == grant_id,
                SourceReference.external_id == external,
            )
        )
        imported = put_evidence(session, task, source, item=item, origin="slack")
        if item is None:
            session.add(
                SourceReference(
                    evidence_id=imported.id,
                    provider="slack",
                    external_id=external,
                    grant_id=grant_id,
                )
            )
        return {"id": imported.id}


def refresh_thread(factory, settings, owner, task_id, evidence_id):
    with factory() as session:
        owned_task(session, task_id, owner)
        item = session.get(Evidence, evidence_id)
        ref = session.get(SourceReference, evidence_id)
        if (
            not item
            or item.task_id != task_id
            or item.removed
            or not ref
            or ref.provider != "slack"
        ):
            raise HTTPException(404, "Slack source not found")
        external, expected = ref.external_id, ref.grant_id
    tokens, grant_id = access(factory, settings, owner)
    if grant_id != expected:
        raise HTTPException(409, "Slack connection changed; remove and import this source again")
    channel, timestamp = external.split("|", 1)
    missing = False
    try:
        source = read_thread(tokens, channel, timestamp)
    except ConnectorFailure as exc:
        if exc.code in ("access_denied", "source_unavailable"):
            missing = True
        else:
            raise failure(factory, owner, grant_id, exc) from exc
    with factory.begin() as session:
        google_sources.grant(session, owner, "slack", grant_id, lock=True)
        task = owned_task(session, task_id, owner, lock=True)
        item = session.get(Evidence, evidence_id, populate_existing=True)
        if item.removed:
            raise HTTPException(409, "Source was removed; reload this workspace")
        if missing:
            item.removed = True
            task.generation += 1
        else:
            put_evidence(session, task, source, item=item)
    return {"removed": missing}
