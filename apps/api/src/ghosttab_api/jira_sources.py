"""Read-only Jira Cloud 3LO with fresh site grants and explicit issue selection."""

import hashlib
import re
import secrets
import time
from typing import Annotated
from urllib.parse import urlencode, urlsplit
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from ghosttab_api import calendar, google_sources
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.connector_adapters import BoundedRead, ConnectorFailure, read_selected
from ghosttab_api.models import (
    Evidence,
    SourceConnection,
    SourceOAuthState,
    SourceReference,
    Task,
    new_id,
)
from ghosttab_api.workspaces import owned_task, put_evidence

router = APIRouter(prefix="/api")
User = Annotated[Principal, Depends(current_user)]
READ_SCOPE = "read:jira-work"
RESOURCES = "https://api.atlassian.com/oauth/token/accessible-resources"


def configured(settings):
    return bool(
        settings.jira_client_id
        and settings.jira_client_secret.get_secret_value()
        and settings.token_encryption_key.get_secret_value()
    )


def begin(factory, settings, owner):
    if not configured(settings):
        raise HTTPException(503, "Jira needs server configuration; see docs/jira-source.md")
    state = secrets.token_urlsafe(32)
    digest = hashlib.sha256(state.encode()).hexdigest()
    with factory.begin() as session:
        if session.get(SourceConnection, (owner, "jira")):
            raise HTTPException(409, "Disconnect Jira before connecting another account")
        session.execute(
            delete(SourceOAuthState).where(
                SourceOAuthState.owner_id == owner, SourceOAuthState.provider == "jira"
            )
        )
        session.add(
            SourceOAuthState(
                digest=digest,
                owner_id=owner,
                provider="jira",
                encrypted_verifier=calendar.encrypt(settings, "confidential-web-client"),
                expires_at=time.time() + 600,
            )
        )
    return "https://auth.atlassian.com/authorize?" + urlencode(
        {
            "audience": "api.atlassian.com",
            "client_id": settings.jira_client_id,
            "scope": READ_SCOPE + " offline_access",
            "redirect_uri": settings.jira_redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }
    ), digest


def exchange(settings, data):
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post(
                "https://auth.atlassian.com/oauth/token",
                json={
                    "client_id": settings.jira_client_id,
                    "client_secret": settings.jira_client_secret.get_secret_value(),
                    **data,
                },
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise HTTPException(503, "Jira authorization is temporarily unavailable")
        if not response.is_success:
            raise HTTPException(401, "Jira authorization expired or was declined; reconnect")
        body = response.json()
        if (
            not isinstance(body.get("access_token"), str)
            or not body["access_token"]
            or not isinstance(body.get("refresh_token"), str)
            or not body["refresh_token"]
            or type(body.get("expires_in")) is not int
            or body["expires_in"] <= 0
            or str(body.get("token_type", "Bearer")).lower() != "bearer"
        ):
            raise ValueError("Incomplete rotating grant")
        return {
            "access_token": body["access_token"],
            "refresh_token": body["refresh_token"],
            "expires_at": time.time() + body["expires_in"],
            "scope": body.get("scope", ""),
        }
    except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError) as exc:
        raise HTTPException(502, "Jira returned incomplete authorization; try again later") from exc


def client_for(token):
    return httpx.Client(
        headers={"Authorization": "Bearer " + token}, timeout=20, follow_redirects=False
    )


def site_origin(value):
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError("Invalid site URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not re.fullmatch(r"[a-z0-9-]+\.atlassian\.net", parsed.hostname or "")
        or parsed.username
        or parsed.password
        or parsed.port
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Unsupported site URL")
    return "https://" + parsed.hostname


def resources(client):
    try:
        response = client.get(RESOURCES, timeout=20, follow_redirects=False)
        if response.status_code == 401:
            raise ConnectorFailure("connection_revoked")
        if response.status_code == 429 or response.status_code >= 500:
            raise ConnectorFailure("provider_unavailable", retryable=True)
        if not response.is_success:
            raise ConnectorFailure("access_denied")
        if len(response.content) > 2_000_000:
            raise ValueError("Oversized resource list")
        body = response.json()
        if not isinstance(body, list) or len(body) > 1000:
            raise ValueError("Invalid resource list")
        result = {}
        for site in body:
            if not isinstance(site, dict) or not isinstance(site.get("scopes"), list):
                raise ValueError("Invalid site scopes")
            if READ_SCOPE not in site["scopes"]:
                continue
            cloud = str(UUID(site["id"]))
            url = site_origin(site["url"])
            if cloud in result and result[cloud]["url"] != url:
                raise ValueError("Ambiguous site")
            result[cloud] = {"id": cloud, "url": url, "name": str(site.get("name") or url)[:200]}
        return list(result.values())
    except httpx.HTTPError as exc:
        raise ConnectorFailure("provider_unavailable", retryable=True) from exc
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise ConnectorFailure("invalid_response") from exc


def reconcile_sites(factory, settings, owner, expected, sites):
    allowed = sorted(site["id"] for site in sites)
    with factory.begin() as session:
        row = google_sources.grant(session, owner, "jira", expected, lock=True)
        tokens = calendar.decrypt(settings, row.encrypted_tokens)
        if tokens.get("site_ids", []) == allowed:
            return row.grant_id
        # A site-access epoch fences in-flight reads; retained sites keep their sources.
        row.grant_id = new_id()
        tokens["site_ids"] = allowed
        row.encrypted_tokens = calendar.encrypt(settings, tokens)
        for task in session.scalars(
            select(Task).where(Task.owner_id == owner).order_by(Task.id).with_for_update()
        ):
            changed = False
            rows = session.execute(
                select(Evidence, SourceReference)
                .join(SourceReference, SourceReference.evidence_id == Evidence.id)
                .where(
                    Evidence.task_id == task.id,
                    Evidence.removed.is_(False),
                    SourceReference.provider == "jira",
                    SourceReference.grant_id == expected,
                )
            ).all()
            for item, ref in rows:
                if ref.external_id.split("|", 1)[0] in allowed:
                    ref.grant_id = row.grant_id
                else:
                    item.removed = True
                    changed = True
            if changed:
                task.generation += 1
        return row.grant_id


def finish(factory, settings, state, cookie, code, error):
    digest = hashlib.sha256(state.encode()).hexdigest()
    if not cookie or not secrets.compare_digest(cookie, digest):
        raise HTTPException(400, "Finish Jira authorization in the browser where it started")
    with factory.begin() as session:
        pending = session.execute(
            delete(SourceOAuthState)
            .where(
                SourceOAuthState.digest == digest,
                SourceOAuthState.provider == "jira",
                SourceOAuthState.expires_at > time.time(),
            )
            .returning(SourceOAuthState.owner_id)
        ).first()
    if not pending or error or not code:
        raise HTTPException(400, "Jira consent expired, was declined or was already used")
    tokens = exchange(
        settings,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.jira_redirect_uri,
        },
    )
    if not isinstance(tokens["scope"], str) or READ_SCOPE not in tokens["scope"].split():
        raise HTTPException(400, "Jira read permissions and offline access are required")
    try:
        with client_for(tokens["access_token"]) as client:
            sites = resources(client)
    except ConnectorFailure as exc:
        raise HTTPException(502, "Could not verify authorized Jira sites; reconnect") from exc
    if not sites:
        raise HTTPException(400, "Authorize at least one readable Jira Cloud site")
    tokens["site_ids"] = sorted(site["id"] for site in sites)
    with factory.begin() as session:
        if session.get(SourceConnection, (pending.owner_id, "jira")):
            raise HTTPException(409, "Jira is already connected")
        session.add(
            SourceConnection(
                owner_id=pending.owner_id,
                provider="jira",
                encrypted_tokens=calendar.encrypt(settings, tokens),
            )
        )


def access(factory, settings, owner):
    grant_id = None
    try:
        with factory.begin() as session:
            row = google_sources.grant(session, owner, "jira", lock=True)
            grant_id = row.grant_id
            tokens = calendar.decrypt(settings, row.encrypted_tokens)
            if tokens["expires_at"] <= time.time() + 60:
                fresh = exchange(
                    settings,
                    {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
                )
                fresh["scope"] = fresh["scope"] or tokens["scope"]
                fresh["site_ids"] = tokens.get("site_ids", [])
                tokens = fresh
                row.encrypted_tokens = calendar.encrypt(settings, tokens)
            if not isinstance(tokens["scope"], str) or READ_SCOPE not in tokens["scope"].split():
                raise HTTPException(401, "Jira read access is missing; reconnect")
        return tokens, grant_id
    except HTTPException as exc:
        if exc.status_code == 401 and grant_id:
            google_sources.disconnect(factory, owner, "jira", expected=grant_id)
        raise


def failure(factory, owner, grant_id, exc):
    if exc.code == "connection_revoked":
        google_sources.disconnect(factory, owner, "jira", expected=grant_id)
        return HTTPException(401, "Jira access was revoked; reconnect")
    if exc.retryable:
        return HTTPException(503, "Jira is unavailable or rate limited; try again later")
    return HTTPException(
        403 if exc.code in ("access_denied", "source_unavailable") else 502,
        "Jira could not provide this site or issue; check access and retry",
    )


def available(factory, settings, owner, tokens, grant_id, client):
    try:
        sites = resources(client)
        current = reconcile_sites(factory, settings, owner, grant_id, sites)
        return sites, current
    except ConnectorFailure as exc:
        raise failure(factory, owner, grant_id, exc) from exc


@router.get("/integrations/jira")
def status(req: Request, user: User):
    with req.app.state.sessions() as session:
        return {
            "configured": configured(req.app.state.settings),
            "connected": session.get(SourceConnection, (user.id, "jira")) is not None,
        }


@router.post("/integrations/jira/start")
def start(req: Request, user: User):
    url, digest = begin(req.app.state.sessions, req.app.state.settings, user.id)
    response = JSONResponse({"url": url})
    response.set_cookie(
        "ghosttab_jira_oauth",
        digest,
        httponly=True,
        samesite="lax",
        secure=req.app.state.settings.environment == "production",
        max_age=600,
        path="/api/integrations/jira/callback",
    )
    return response


@router.get("/integrations/jira/callback")
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
            req.cookies.get("ghosttab_jira_oauth"),
            code,
            error,
        )
    except HTTPException:
        outcome = "connection_failed"
    response = RedirectResponse(
        req.app.state.settings.frontend_url + "?source=jira&result=" + outcome, status_code=303
    )
    response.delete_cookie("ghosttab_jira_oauth", path="/api/integrations/jira/callback")
    return response


@router.delete("/integrations/jira", status_code=204)
def disconnect(req: Request, user: User):
    google_sources.disconnect(req.app.state.sessions, user.id, "jira")


@router.get("/integrations/jira/sites")
def list_sites(req: Request, user: User):
    factory, settings = req.app.state.sessions, req.app.state.settings
    tokens, grant_id = access(factory, settings, user.id)
    with client_for(tokens["access_token"]) as client:
        sites, _ = available(factory, settings, user.id, tokens, grant_id, BoundedRead(client))
    return {"sites": sites[:50], "has_more": len(sites) > 50}


class IssueSelection(BaseModel):
    cloud_id: UUID
    issue_key: str = Field(pattern=r"^[A-Z][A-Z0-9_]*-[0-9]+$", max_length=128)


def issue_source(client, site, key):
    source = read_selected(client, "jira", key, container_id=site["id"])
    return source.evidence.model_copy(update={"url": site["url"] + "/browse/" + key})


@router.post("/tasks/{task_id}/imports/jira")
def import_issue(task_id: str, body: IssueSelection, req: Request, user: User):
    factory, settings = req.app.state.sessions, req.app.state.settings
    with factory() as session:
        owned_task(session, task_id, user.id)
    tokens, grant_id = access(factory, settings, user.id)
    with client_for(tokens["access_token"]) as client:
        reader = BoundedRead(client)
        sites, grant_id = available(factory, settings, user.id, tokens, grant_id, reader)
        site = next((site for site in sites if site["id"] == str(body.cloud_id)), None)
        if site is None:
            raise HTTPException(403, "Choose a site currently authorized for this Jira connection")
        try:
            source = issue_source(reader, site, body.issue_key)
        except ConnectorFailure as exc:
            raise failure(factory, user.id, grant_id, exc) from exc
    with factory.begin() as session:
        google_sources.grant(session, user.id, "jira", grant_id, lock=True)
        task = owned_task(session, task_id, user.id, lock=True)
        external = str(body.cloud_id) + "|" + body.issue_key
        item = session.scalar(
            select(Evidence)
            .join(SourceReference, SourceReference.evidence_id == Evidence.id)
            .where(
                Evidence.task_id == task_id,
                Evidence.removed.is_(False),
                SourceReference.provider == "jira",
                SourceReference.grant_id == grant_id,
                SourceReference.external_id == external,
            )
        )
        imported = put_evidence(session, task, source, item=item, origin="jira")
        if item is None:
            session.add(
                SourceReference(
                    evidence_id=imported.id,
                    provider="jira",
                    external_id=external,
                    grant_id=grant_id,
                )
            )
        return {"id": imported.id}


def refresh_issue(factory, settings, owner, task_id, evidence_id):
    with factory() as session:
        owned_task(session, task_id, owner)
        item = session.get(Evidence, evidence_id)
        ref = session.get(SourceReference, evidence_id)
        if not item or item.task_id != task_id or item.removed or not ref or ref.provider != "jira":
            raise HTTPException(404, "Jira source not found")
        external, expected = ref.external_id, ref.grant_id
    tokens, grant_id = access(factory, settings, owner)
    if grant_id != expected:
        raise HTTPException(409, "Jira connection changed; remove and import this issue again")
    cloud, key = external.split("|", 1)
    missing = False
    with client_for(tokens["access_token"]) as client:
        reader = BoundedRead(client)
        sites, grant_id = available(factory, settings, owner, tokens, grant_id, reader)
        site = next((site for site in sites if site["id"] == cloud), None)
        if site is None:
            return {"removed": True}
        try:
            source = issue_source(reader, site, key)
        except ConnectorFailure as exc:
            if exc.code in ("source_unavailable", "access_denied"):
                missing = True
            else:
                raise failure(factory, owner, grant_id, exc) from exc
    with factory.begin() as session:
        google_sources.grant(session, owner, "jira", grant_id, lock=True)
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
