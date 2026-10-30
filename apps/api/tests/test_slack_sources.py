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
from ghosttab_api import slack_sources as slack
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.models import SourceConnection
from ghosttab_api.worker import run_once

system = test_workspaces.system


def tokens(**updates):
    return {
        "access_token": "synthetic-slack",
        "refresh_token": "",
        "expires_at": None,
        "scope": "channels:read,channels:history",
        "team_id": "TDEMO123",
        **updates,
    }


def connected(system, **updates):
    with system.factory.begin() as session:
        row = SourceConnection(
            owner_id="alice",
            provider="slack",
            encrypted_tokens=calendar.encrypt(system.settings, tokens(**updates)),
        )
        session.add(row)
        session.flush()
        return row.grant_id


def transport(
    monkeypatch,
    *,
    private=False,
    text="Support contact is unassigned.",
    error=None,
    after_read=None,
):
    calls = []

    def respond(req):
        calls.append(req)
        assert req.method == "GET" and req.headers["Authorization"] == "Bearer synthetic-slack"
        if error:
            return httpx.Response(200, json={"ok": False, "error": error})
        if req.url.path.endswith("conversations.info"):
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "channel": {"id": "CDEMO123", "name": "demo-launch", "is_private": private},
                },
            )
        assert req.url.params["limit"] == "15"
        if after_read:
            after_read()
        return httpx.Response(
            200, json={"ok": True, "messages": [{"ts": "1234567890.000001", "text": text}]}
        )

    monkeypatch.setattr(
        slack,
        "client_for",
        lambda token: httpx.Client(
            headers={"Authorization": "Bearer " + token}, transport=httpx.MockTransport(respond)
        ),
    )
    return calls


def task(system):
    return system.request(
        "POST", "/tasks", {"title": "Fictional Slack task", "goal": "Review selected thread."}
    ).json()["id"]


def selection():
    return {"channel_id": "CDEMO123", "thread_ts": "1234567890.000001"}


def test_slack_web_oauth_is_owner_browser_bound_and_single_use(system, monkeypatch):
    system.settings.slack_client_id = "test-client"
    system.settings.slack_client_secret = SecretStr("test-secret")
    response = system.request("POST", "/integrations/slack/start")
    assert response.status_code == 200
    query = parse_qs(urlparse(response.json()["url"]).query)
    assert set(query["user_scope"][0].split(",")) == slack.SCOPES
    assert "scope" not in query
    state = query["state"][0]
    cookie = hashlib.sha256(state.encode()).hexdigest()
    monkeypatch.setattr(slack, "exchange", lambda *_: tokens())
    with pytest.raises(HTTPException):
        slack.finish(system.factory, system.settings, state, "wrong", "code", "")
    slack.finish(system.factory, system.settings, state, cookie, "code", "")
    with pytest.raises(HTTPException):
        slack.finish(system.factory, system.settings, state, cookie, "code", "")
    with system.factory() as session:
        assert (
            "synthetic-slack"
            not in session.get(SourceConnection, ("alice", "slack")).encrypted_tokens
        )


def test_slack_import_refresh_citations_disconnect_and_duplicate_selection(system, monkeypatch):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    path = f"/tasks/{tid}/imports/slack"
    response = system.request("POST", path, selection())
    assert response.status_code == 200
    eid = response.json()["id"]
    assert system.request("POST", path, selection()).json()["id"] == eid
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    original = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert original["task"]["source_count"] == 1 and original["task"]["freshness"] == "current"
    transport(monkeypatch, text="Maya is now the support contact.")
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 200
    updated = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert updated["snapshot"] == original["snapshot"] and updated["task"]["freshness"] == "stale"
    assert system.request("DELETE", "/integrations/slack").status_code == 204
    removed = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert removed["snapshot"] is None and removed["evidence"] == []


def test_private_channels_and_other_owners_never_reach_thread_content(system, monkeypatch):
    connected(system)
    calls = transport(monkeypatch, private=True)
    tid = task(system)
    assert system.request("POST", f"/tasks/{tid}/imports/slack", selection()).status_code == 403
    assert len(calls) == 1 and calls[0].url.path.endswith("conversations.info")
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert system.request("POST", f"/tasks/{tid}/imports/slack", selection()).status_code == 404
    assert len(calls) == 1


def test_disconnect_during_slack_read_cannot_publish(system, monkeypatch):
    connected(system)
    transport(
        monkeypatch, after_read=lambda: google_sources.disconnect(system.factory, "alice", "slack")
    )
    tid = task(system)
    assert system.request("POST", f"/tasks/{tid}/imports/slack", selection()).status_code == 409
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


def test_rotating_slack_user_token_refreshes_and_preserves_team_identity(system, monkeypatch):
    connected(system, expires_at=time.time() - 1, refresh_token="old-refresh")
    monkeypatch.setattr(
        slack,
        "exchange",
        lambda *args, **kwargs: tokens(
            refresh_token="new-refresh", expires_at=time.time() + 3600, team_id=""
        ),
    )
    value, _ = slack.access(system.factory, system.settings, "alice")
    assert value["team_id"] == "TDEMO123" and value["refresh_token"] == "new-refresh"
    with system.factory() as session:
        saved = calendar.decrypt(
            system.settings, session.get(SourceConnection, ("alice", "slack")).encrypted_tokens
        )
        assert saved["refresh_token"] == "new-refresh"


def test_rate_limit_preserves_context_but_revoked_token_blocks_it(system, monkeypatch):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request("POST", f"/tasks/{tid}/imports/slack", selection()).json()["id"]
    transport(monkeypatch, error="ratelimited")
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 503
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"]
    transport(monkeypatch, error="token_revoked")
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 401
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


def test_oauth_requires_user_read_scopes_not_a_bot_token(system, monkeypatch):
    original = httpx.Client
    body = {
        "ok": True,
        "team": {"id": "TDEMO123"},
        "authed_user": {
            "token_type": "user",
            "access_token": "synthetic-slack",
            "scope": "channels:history,channels:read",
        },
    }
    monkeypatch.setattr(
        slack.httpx,
        "Client",
        lambda **kwargs: original(
            **kwargs, transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
        ),
    )
    assert slack.exchange(system.settings, {"code": "synthetic-code"})["team_id"] == "TDEMO123"
    body["authed_user"]["scope"] = "channels:read"
    with pytest.raises(HTTPException, match="public-channel read"):
        slack.exchange(system.settings, {"code": "synthetic-code"})
    body["authed_user"]["scope"] = "channels:history,channels:read"
    body["authed_user"]["token_type"] = "bot"
    with pytest.raises(HTTPException, match="user read access"):
        slack.exchange(system.settings, {"code": "synthetic-code"})


def test_channel_becoming_private_blocks_saved_source_and_dependent_brief(system, monkeypatch):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request("POST", f"/tasks/{tid}/imports/slack", selection()).json()["id"]
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    calls = transport(monkeypatch, private=True)
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").json() == {
        "removed": True
    }
    result = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert result["snapshot"] is None and result["evidence"] == []
    assert len(calls) == 1
