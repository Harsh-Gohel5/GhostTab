import base64
import hashlib
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import quote, urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy import delete, select, update

from ghosttab_api.contracts import EvidenceInput
from ghosttab_api.models import Connection, Evidence, OAuthState, Task

SCOPE = "https://www.googleapis.com/auth/calendar.events.readonly"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def cipher(settings):
    try:
        return Fernet(settings.token_encryption_key.get_secret_value().encode())
    except (ValueError, TypeError) as exc:
        raise HTTPException(503, "Calendar token encryption needs configuration") from exc


def encrypt(settings, value):
    return cipher(settings).encrypt(json.dumps(value).encode()).decode()


def decrypt(settings, value):
    try:
        return json.loads(cipher(settings).decrypt(value.encode()))
    except (InvalidToken, ValueError) as exc:
        raise HTTPException(
            503, "Calendar credentials could not be opened; check encryption key"
        ) from exc


def begin_connection(factory, settings, owner_id):
    if not settings.google_ready:
        raise HTTPException(503, "Google Calendar needs server configuration; see docs/setup.md")
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    digest = hashlib.sha256(state.encode()).hexdigest()
    with factory.begin() as session:
        if session.get(Connection, owner_id):
            raise HTTPException(409, "Disconnect the existing calendar before connecting another")
        session.execute(delete(OAuthState).where(OAuthState.owner_id == owner_id))
        session.add(
            OAuthState(
                digest=digest,
                owner_id=owner_id,
                encrypted_verifier=encrypt(settings, verifier),
                expires_at=time.time() + 600,
            )
        )
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=")
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "code_challenge": challenge.decode(),
            "code_challenge_method": "S256",
        }
    )
    return "https://accounts.google.com/o/oauth2/v2/auth?" + query, digest


def token_exchange(settings, data):
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret.get_secret_value(),
                    **data,
                },
            )
        if response.status_code in (400, 401):
            raise HTTPException(401, "Google authorization expired or was declined; reconnect")
        if not response.is_success:
            raise HTTPException(502, "Google authorization is temporarily unavailable")
        result = response.json()
        if not isinstance(result.get("access_token"), str):
            raise ValueError("Missing access token")
        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
            "expires_at": time.time() + int(result.get("expires_in", 3600)),
            "scope": result.get("scope", ""),
        }
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Could not complete Google authorization") from exc


def finish_connection(factory, settings, state, cookie, code, error):
    digest = hashlib.sha256(state.encode()).hexdigest()
    if not cookie or not secrets.compare_digest(digest, cookie):
        raise HTTPException(
            400, "Calendar authorization must finish in the browser where it started"
        )
    with factory.begin() as session:
        pending = session.execute(
            delete(OAuthState)
            .where(OAuthState.digest == digest, OAuthState.expires_at > time.time())
            .returning(OAuthState.owner_id, OAuthState.encrypted_verifier)
        ).first()
    if not pending:
        raise HTTPException(400, "Calendar authorization expired or was already used")
    if error or not code:
        raise HTTPException(400, "Calendar permission was not granted")
    tokens = token_exchange(
        settings,
        {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri,
            "code_verifier": decrypt(settings, pending.encrypted_verifier),
        },
    )
    if SCOPE not in tokens["scope"].split() or not tokens["refresh_token"]:
        raise HTTPException(400, "Read access and offline authorization are required; reconnect")
    with factory.begin() as session:
        if session.get(Connection, pending.owner_id):
            raise HTTPException(409, "A calendar is already connected")
        session.add(
            Connection(owner_id=pending.owner_id, encrypted_tokens=encrypt(settings, tokens))
        )


def disconnect(factory, owner_id, *, expected=None):
    with factory.begin() as session:
        session.execute(
            update(Connection)
            .where(Connection.owner_id == owner_id)
            .values(updated_at=Connection.updated_at)
        )
        current = session.get(Connection, owner_id, populate_existing=True)
        if expected is not None and (not current or current.grant_id != expected):
            return
        # Block derived content and queued work immediately when access is removed.
        tasks = session.scalars(
            select(Task)
            .where(Task.owner_id == owner_id, Task.calendar_event_id.is_not(None))
            .with_for_update()
        ).all()
        for task in tasks:
            task.generation += 1
            task.title = "Disconnected meeting"
            task.calendar_event_id = None
            session.execute(
                update(Evidence)
                .where(Evidence.task_id == task.id, Evidence.origin == "google_calendar")
                .values(removed=True)
            )
        session.execute(delete(Connection).where(Connection.owner_id == owner_id))
        session.execute(delete(OAuthState).where(OAuthState.owner_id == owner_id))


def check_grant(session, owner_id, grant_id, *, lock=False):
    if lock:
        session.execute(
            update(Connection)
            .where(Connection.owner_id == owner_id)
            .values(updated_at=Connection.updated_at)
        )
    connection = session.get(Connection, owner_id)
    if not connection or connection.grant_id != grant_id:
        raise HTTPException(409, "Calendar access changed; reconnect and try again")


def calendar_request(factory, settings, owner_id, event_id=None):
    with factory() as session:
        connection = session.get(Connection, owner_id)
        if not connection:
            raise HTTPException(409, "Connect Google Calendar first")
        encrypted, grant_id = connection.encrypted_tokens, connection.grant_id
    tokens = decrypt(settings, encrypted)
    if tokens["expires_at"] <= time.time() + 60:
        try:
            fresh = token_exchange(
                settings, {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
            )
        except HTTPException as exc:
            if exc.status_code == 401:
                disconnect(factory, owner_id, expected=grant_id)
            raise
        fresh["refresh_token"] = fresh["refresh_token"] or tokens["refresh_token"]
        fresh["scope"] = fresh["scope"] or tokens["scope"]
        tokens = fresh
        with factory.begin() as session:
            changed = session.execute(
                update(Connection)
                .where(
                    Connection.owner_id == owner_id,
                    Connection.grant_id == grant_id,
                    Connection.encrypted_tokens == encrypted,
                )
                .values(encrypted_tokens=encrypt(settings, tokens), updated_at=time.time())
            ).rowcount
            if not changed:
                raise HTTPException(409, "Calendar access changed; try again")
    now = datetime.now(UTC)
    params = {
        "timeMin": now.isoformat(),
        "timeMax": (now + timedelta(days=14)).isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": 25,
        "fields": "items(id,summary,start,end,status),nextPageToken",
    }
    url = EVENTS_URL + ("/" + quote(event_id, safe="") if event_id else "")
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            response = client.get(
                url,
                params={
                    "fields": "id,summary,description,start,end,location,htmlLink,status,updated"
                }
                if event_id
                else params,
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        if response.status_code == 403:
            try:
                reasons = [
                    x.get("reason") for x in response.json().get("error", {}).get("errors", [])
                ]
            except (ValueError, AttributeError, TypeError):
                reasons = []
            if any(
                x in ("rateLimitExceeded", "userRateLimitExceeded", "quotaExceeded")
                for x in reasons
            ):
                raise HTTPException(503, "Calendar rate limit reached; wait before checking again")
        if response.status_code in (401, 403):
            disconnect(factory, owner_id, expected=grant_id)
            raise HTTPException(401, "Calendar access is unavailable; reconnect Google Calendar")
        if response.status_code in (404, 410):
            return {"status": "cancelled", "id": event_id}, grant_id
        if not response.is_success:
            raise HTTPException(502, "Calendar is temporarily unavailable; try again later")
        result = response.json()
        with factory() as session:
            check_grant(session, owner_id, grant_id)
        return result, grant_id
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Could not read Calendar; try again later") from exc


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def event_evidence(event):
    parser = PlainText()
    parser.feed(str(event.get("description", ""))[:30000])
    title = str(event.get("summary") or "Untitled meeting")[:200]
    start, end = event.get("start", {}), event.get("end", {})
    # No attachment fetching, attendee email ingestion or arbitrary source URL requests.
    content = "\n".join(
        [
            f"Meeting: {title}",
            f"Starts: {start.get('dateTime', start.get('date', 'Unknown'))}",
            f"Ends: {end.get('dateTime', end.get('date', 'Unknown'))}",
            f"Timezone: {start.get('timeZone', 'Use the offset in the start time')}",
            f"Location: {str(event.get('location', 'Not provided'))[:1000]}",
            "Description: " + " ".join(parser.parts),
        ]
    )[:12000]
    url = str(event.get("htmlLink", ""))[:2000]
    return EvidenceInput(
        title=title, content=content, url=url if url.startswith("https://") else ""
    )
