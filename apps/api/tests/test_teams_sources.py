import base64
import hashlib
import time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import test_workspaces
from connector_samples import SampleModel
from fastapi import HTTPException
from pydantic import SecretStr

from ghosttab_api import calendar, google_sources
from ghosttab_api import teams_sources as teams
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.models import SourceConnection, SourceOAuthState
from ghosttab_api.worker import run_once

system = test_workspaces.system
TENANT = "11111111-1111-4111-8111-111111111111"
CHAT = "19:demo@thread.v2"


def tokens(**updates):
    return {
        "access_token": "synthetic-teams",
        "refresh_token": "synthetic-refresh",
        "expires_at": time.time() + 3600,
        "scope": "Chat.Read",
        "tenant_id": TENANT,
        **updates,
    }


def configured(system):
    system.settings.teams_tenant_id = TENANT
    system.settings.teams_client_id = "synthetic-client"
    system.settings.teams_client_secret = SecretStr("synthetic-secret")


def connected(system, **updates):
    configured(system)
    with system.factory.begin() as session:
        row = SourceConnection(
            owner_id="alice",
            provider="teams",
            encrypted_tokens=calendar.encrypt(system.settings, tokens(**updates)),
        )
        session.add(row)
        session.flush()
        return row.grant_id


def transport(
    monkeypatch,
    *,
    text="Approval is pending.",
    code=200,
    after_read=None,
    empty=False,
    malformed=False,
    next_page=False,
):
    calls = []

    def respond(req):
        calls.append(req)
        assert req.method == "GET" and req.url.host == "graph.microsoft.com"
        assert req.url.path.startswith("/v1.0/me/chats/")
        assert req.headers["Authorization"] == "Bearer synthetic-teams"
        if not req.url.path.endswith("/messages"):
            return httpx.Response(
                code, json={"id": CHAT, "chatType": "group", "topic": "Fictional launch chat"}
            )
        assert (
            req.url.params["$top"] == "50" and req.url.params["$orderby"] == "createdDateTime desc"
        )
        if after_read:
            after_read()
        body = {
            "value": []
            if empty
            else [
                {
                    "id": "1",
                    "body": {"contentType": "html", "content": f"<p>{text}</p>"},
                    "from": {"user": {"displayName": "Maya"}},
                    "createdDateTime": "2026-11-02T10:00:00-07:00",
                }
            ]
        }
        if malformed:
            body = {"value": "not a list"}
        if next_page:
            body["@odata.nextLink"] = "https://evil.test/never-follow"
        return httpx.Response(200, json=body)

    monkeypatch.setattr(
        teams,
        "client_for",
        lambda token: httpx.Client(
            headers={"Authorization": "Bearer " + token}, transport=httpx.MockTransport(respond)
        ),
    )
    return calls


def task(system):
    return system.request(
        "POST", "/tasks", {"title": "Fictional Teams task", "goal": "Prepare selected chat."}
    ).json()["id"]


def test_oauth_pkce_browser_owner_binding_and_single_use(system, monkeypatch):
    configured(system)
    result = system.request("POST", "/integrations/teams/start")
    assert result.status_code == 200
    query = parse_qs(urlparse(result.json()["url"]).query)
    assert set(query["scope"][0].split()) == {teams.SCOPE, "offline_access"}
    assert query["code_challenge_method"] == ["S256"]
    state = query["state"][0]
    digest = hashlib.sha256(state.encode()).hexdigest()
    with system.factory() as session:
        saved = calendar.decrypt(
            system.settings, session.get(SourceOAuthState, digest).encrypted_verifier
        )
    assert query["code_challenge"] == [
        base64.urlsafe_b64encode(hashlib.sha256(saved["verifier"].encode()).digest())
        .rstrip(b"=")
        .decode()
    ]

    def exchange(settings, data):
        assert data["code_verifier"] == saved["verifier"]
        return tokens()

    monkeypatch.setattr(teams, "exchange", exchange)
    with pytest.raises(HTTPException):
        teams.finish(system.factory, system.settings, state, "wrong", "code", "")
    teams.finish(system.factory, system.settings, state, digest, "code", "")
    with pytest.raises(HTTPException):
        teams.finish(system.factory, system.settings, state, digest, "code", "")
    with system.factory() as session:
        assert (
            "synthetic-teams"
            not in session.get(SourceConnection, ("alice", "teams")).encrypted_tokens
        )


def test_import_dedup_refresh_citations_disconnect(system, monkeypatch):
    connected(system)
    transport(monkeypatch, next_page=True)
    tid = task(system)
    path = f"/tasks/{tid}/imports/teams"
    result = system.request("POST", path, {"chat_id": CHAT})
    assert result.status_code == 200, result.text
    eid = result.json()["id"]
    assert system.request("POST", path, {"chat_id": CHAT}).json()["id"] == eid
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    original = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert original["snapshot"] and original["task"]["source_count"] == 1
    assert (
        "Maya" in original["evidence"][0]["content"]
        and "incomplete" in original["evidence"][0]["content"].lower()
    )
    transport(monkeypatch, text="Approval was deferred.")
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 200
    updated = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert updated["task"]["freshness"] == "stale" and updated["snapshot"] == original["snapshot"]
    assert system.request("DELETE", "/integrations/teams").status_code == 204
    removed = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert removed["evidence"] == [] and removed["snapshot"] is None


def test_other_owner_invalid_chat_and_metadata_denial_do_not_read_messages(system, monkeypatch):
    connected(system)
    calls = transport(monkeypatch, code=403)
    tid = task(system)
    path = f"/tasks/{tid}/imports/teams"
    assert system.request("POST", path, {"chat_id": CHAT}).status_code == 403
    assert len(calls) == 1
    assert system.request("POST", path, {"chat_id": "https://evil.test"}).status_code == 422
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert system.request("POST", path, {"chat_id": CHAT}).status_code == 404
    assert len(calls) == 1


def test_disconnect_during_read_cannot_publish(system, monkeypatch):
    connected(system)
    transport(
        monkeypatch, after_read=lambda: google_sources.disconnect(system.factory, "alice", "teams")
    )
    tid = task(system)
    assert (
        system.request("POST", f"/tasks/{tid}/imports/teams", {"chat_id": CHAT}).status_code == 409
    )
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


@pytest.mark.parametrize(
    "code,expected", [(429, 503), (500, 503), (401, 401), (403, 200), (404, 200)]
)
def test_transient_failure_preserves_context_permission_loss_blocks(
    system, monkeypatch, code, expected
):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request("POST", f"/tasks/{tid}/imports/teams", {"chat_id": CHAT}).json()["id"]
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    transport(monkeypatch, code=code)
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == expected
    result = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert bool(result["evidence"]) == (expected == 503)
    assert bool(result["snapshot"]) == (expected == 503)


def test_empty_chat_blocks_old_text_but_malformed_response_preserves_it(system, monkeypatch):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request("POST", f"/tasks/{tid}/imports/teams", {"chat_id": CHAT}).json()["id"]
    path = f"/tasks/{tid}/evidence/{eid}/refresh"
    transport(monkeypatch, malformed=True)
    assert system.request("POST", path).status_code == 502
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"]
    transport(monkeypatch, empty=True)
    assert system.request("POST", path).json() == {"removed": True}
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


def test_refresh_preserves_optional_token_scope_and_rejects_changed_tenant(system, monkeypatch):
    connected(system, expires_at=time.time() - 1)
    monkeypatch.setattr(teams, "exchange", lambda *_: tokens(refresh_token="", scope=""))
    value, _ = teams.access(system.factory, system.settings, "alice")
    assert value["refresh_token"] == "synthetic-refresh" and value["scope"] == "Chat.Read"
    system.settings.teams_tenant_id = "22222222-2222-4222-8222-222222222222"
    with pytest.raises(HTTPException):
        teams.access(system.factory, system.settings, "alice")
    assert not system.request("GET", "/integrations/teams").json()["connected"]


def test_exchange_uses_tenant_fixed_endpoint_form_secret_and_safe_errors(system, monkeypatch):
    configured(system)
    original = httpx.Client
    body = {
        "access_token": "synthetic",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "Chat.Read",
    }
    code = 200

    def respond(req):
        assert str(req.url) == f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
        form = parse_qs(req.content.decode())
        assert form["client_secret"] == ["synthetic-secret"] and form["scope"] == [
            teams.SCOPE + " offline_access"
        ]
        return httpx.Response(code, json=body)

    monkeypatch.setattr(
        teams.httpx,
        "Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    assert (
        teams.exchange(system.settings, {"grant_type": "refresh_token"})["access_token"]
        == "synthetic"
    )
    code = 400
    body = {"error": "invalid_grant", "error_description": "private provider detail"}
    with pytest.raises(HTTPException) as result:
        teams.exchange(system.settings, {})
    assert result.value.status_code == 401 and "private" not in result.value.detail


@pytest.mark.parametrize("scope", ["User.Read", "Chat.ReadWrite", "", None])
def test_exact_read_scope_required(scope):
    assert not teams.readable(scope)


@pytest.mark.parametrize(
    "updates", [{"expires_at": None}, {"access_token": 1}, {"refresh_token": ""}, {"scope": []}]
)
def test_malformed_saved_grant_returns_reconnect_and_blocks_sources(system, updates):
    connected(system, **updates)
    with pytest.raises(HTTPException) as result:
        teams.access(system.factory, system.settings, "alice")
    assert result.value.status_code == 401
    assert not system.request("GET", "/integrations/teams").json()["connected"]
