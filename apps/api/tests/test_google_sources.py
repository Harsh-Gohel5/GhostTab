import copy
import time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import test_workspaces
from connector_samples import RESPONSES, SampleModel
from fastapi import HTTPException
from sqlalchemy import select

from ghosttab_api import calendar
from ghosttab_api import google_sources as sources
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.models import Connection, SourceConnection, SourceOAuthState
from ghosttab_api.worker import run_once

system = test_workspaces.system


def connected(system, provider="google_docs", *, expired=False):
    with system.factory.begin() as session:
        row = SourceConnection(
            owner_id="alice",
            provider=provider,
            encrypted_tokens=calendar.encrypt(
                system.settings,
                {
                    "access_token": "synthetic-access",
                    "refresh_token": "keep-refresh",
                    "scope": sources.SCOPES[provider],
                    "expires_at": time.time() + (-1 if expired else 3600),
                },
            ),
        )
        session.add(row)
        session.flush()
        return row.grant_id


def transport(monkeypatch, handler=None):
    seen = []

    def respond(req):
        seen.append(req)
        assert req.headers["Authorization"] == "Bearer synthetic-access"
        assert req.method == "GET"
        return handler(req) if handler else httpx.Response(200, json=RESPONSES[req.url.host])

    monkeypatch.setattr(
        sources,
        "client_for",
        lambda token: httpx.Client(
            headers={"Authorization": "Bearer " + token}, transport=httpx.MockTransport(respond)
        ),
    )
    return seen


def task(system):
    return system.request(
        "POST", "/tasks", {"title": "Synthetic cross-tool task", "goal": "Check selected evidence."}
    ).json()["id"]


def test_oauth_is_separate_scoped_bound_and_single_use(system, monkeypatch):
    with system.factory.begin() as session:
        session.add(Connection(owner_id="alice", encrypted_tokens="unchanged-calendar"))
    result = system.request("POST", "/integrations/google/google_docs/start")
    assert result.status_code == 200
    query = parse_qs(urlparse(result.json()["url"]).query)
    assert query["scope"] == [sources.SCOPES["google_docs"]]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"][0].endswith("/google_docs/callback")
    state = query["state"][0]
    with system.factory() as session:
        pending = session.scalar(select(SourceOAuthState))
        digest = pending.digest
        assert state not in pending.encrypted_verifier
    monkeypatch.setattr(
        calendar,
        "token_exchange",
        lambda *_: {
            "access_token": "synthetic-access",
            "refresh_token": "refresh",
            "expires_at": time.time() + 3600,
            "scope": sources.SCOPES["google_docs"],
        },
    )
    for provider, cookie in [("gmail", digest), ("google_docs", "wrong-cookie")]:
        with pytest.raises(HTTPException):
            sources.finish(system.factory, system.settings, provider, state, cookie, "code", "")
    sources.finish(system.factory, system.settings, "google_docs", state, digest, "code", "")
    with pytest.raises(HTTPException):
        sources.finish(system.factory, system.settings, "google_docs", state, digest, "code", "")
    with system.factory() as session:
        assert session.get(Connection, "alice").encrypted_tokens == "unchanged-calendar"
        assert (
            "synthetic-access"
            not in session.get(SourceConnection, ("alice", "google_docs")).encrypted_tokens
        )
    assert system.request("GET", "/integrations/google/google_docs").json()["connected"]
    assert system.request("GET", "/integrations/google/gmail").json()["connected"] is False


def test_missing_scope_or_offline_token_is_not_accepted(system, monkeypatch):
    for scope, refresh in [
        (sources.SCOPES["gmail"], "refresh"),
        (sources.SCOPES["google_docs"], ""),
    ]:
        url, cookie = sources.begin(system.factory, system.settings, "alice", "google_docs")
        state = parse_qs(urlparse(url).query)["state"][0]
        monkeypatch.setattr(
            calendar,
            "token_exchange",
            lambda *_, refresh=refresh, scope=scope: {
                "access_token": "synthetic-access",
                "refresh_token": refresh,
                "expires_at": time.time() + 3600,
                "scope": scope,
            },
        )
        with pytest.raises(HTTPException):
            sources.finish(
                system.factory, system.settings, "google_docs", state, cookie, "code", ""
            )
    assert not system.request("GET", "/integrations/google/google_docs").json()["connected"]


def test_selected_import_refresh_citations_and_disconnect(system, monkeypatch):
    connected(system)
    connected(system, "gmail")
    seen = transport(monkeypatch)
    tid = task(system)
    path = f"/tasks/{tid}/imports/google_docs"
    imported = system.request("POST", path, {"item_id": "synthetic_doc"})
    assert imported.status_code == 200
    eid = imported.json()["id"]
    system.request("POST", path, {"item_id": "synthetic_doc"})
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["task"]["source_count"] == 1
    assert (
        system.request(
            "PUT",
            f"/tasks/{tid}/evidence/{eid}",
            {"title": "Spoofed", "content": "Changed", "url": ""},
        ).status_code
        == 409
    )
    assert (
        system.request("POST", f"/tasks/{tid}/imports/gmail", {"item_id": "aabbcc"}).status_code
        == 200
    )
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    workspace = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert workspace["task"]["freshness"] == "current"
    old = workspace["snapshot"]
    changed = copy.deepcopy(RESPONSES["docs.googleapis.com"])
    changed["title"] = "Updated fictional brief"
    transport(monkeypatch, lambda req: httpx.Response(200, json=changed))
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 200
    updated = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert updated["task"]["freshness"] == "stale"
    assert updated["snapshot"] == old
    change = updated["source_changes"][0]
    assert change["kind"] == "updated" and change["current"]["id"] == eid
    assert change["previous"]["title"] != change["current"]["title"]
    assert change["changed_fields"] == ["title"]
    assert system.request("DELETE", "/integrations/google/google_docs").status_code == 204
    blocked = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert blocked["snapshot"] is None
    assert blocked["source_changes"] == []
    assert [x["origin"] for x in blocked["evidence"]] == ["gmail"]
    assert system.request("GET", "/integrations/google/gmail").json()["connected"]
    assert seen[0].url.host == "docs.googleapis.com"


def test_owner_checks_and_disconnect_during_import(system, monkeypatch):
    connected(system)
    tid = task(system)
    seen = transport(monkeypatch)
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert (
        system.request(
            "POST", f"/tasks/{tid}/imports/google_docs", {"item_id": "synthetic_doc"}
        ).status_code
        == 404
    )
    assert not seen
    system.app.dependency_overrides[current_user] = lambda: Principal("alice")

    def revoke(req):
        sources.disconnect(system.factory, "alice", "google_docs")
        return httpx.Response(200, json=RESPONSES["docs.googleapis.com"])

    transport(monkeypatch, revoke)
    assert (
        system.request(
            "POST", f"/tasks/{tid}/imports/google_docs", {"item_id": "synthetic_doc"}
        ).status_code
        == 409
    )
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


def test_mail_search_only_returns_selected_metadata(system, monkeypatch):
    connected(system, "gmail")

    def respond(req):
        if req.url.path.endswith("/messages"):
            assert req.url.params["q"] == "subject:launch"
            assert req.url.params["maxResults"] == "5"
            return httpx.Response(
                200, json={"messages": [{"id": "aabbcc"}], "nextPageToken": "more"}
            )
        assert req.url.params["format"] == "metadata"
        return httpx.Response(200, json=RESPONSES["gmail.googleapis.com"])

    transport(monkeypatch, respond)
    result = system.request("GET", "/integrations/gmail/messages?q=subject:launch")
    assert result.status_code == 200
    assert result.json() == {
        "messages": [{"id": "aabbcc", "title": "Fictional approval request"}],
        "has_more": True,
    }
    assert system.request("GET", "/tasks").json() == []


def test_refresh_token_preserved_and_revocation_blocks_sources(system, monkeypatch):
    connected(system, expired=True)
    monkeypatch.setattr(
        calendar,
        "token_exchange",
        lambda *_: {
            "access_token": "synthetic-access",
            "refresh_token": "",
            "expires_at": time.time() + 3600,
            "scope": "",
        },
    )
    token, _ = sources.access(system.factory, system.settings, "alice", "google_docs")
    assert token == "synthetic-access"
    with system.factory() as session:
        tokens = calendar.decrypt(
            system.settings,
            session.get(SourceConnection, ("alice", "google_docs")).encrypted_tokens,
        )
        assert tokens["refresh_token"] == "keep-refresh"
    transport(monkeypatch)
    tid = task(system)
    system.request("POST", f"/tasks/{tid}/imports/google_docs", {"item_id": "synthetic_doc"})
    with system.factory.begin() as session:
        row = session.get(SourceConnection, ("alice", "google_docs"))
        tokens["expires_at"] = 0
        row.encrypted_tokens = calendar.encrypt(system.settings, tokens)

    def revoked(*_):
        raise HTTPException(401, "Reconnect")

    monkeypatch.setattr(calendar, "token_exchange", revoked)
    assert (
        system.request(
            "POST", f"/tasks/{tid}/imports/google_docs", {"item_id": "synthetic_doc"}
        ).status_code
        == 401
    )
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


def test_missing_source_is_blocked_and_transient_failure_preserves_it(system, monkeypatch):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request(
        "POST", f"/tasks/{tid}/imports/google_docs", {"item_id": "synthetic_doc"}
    ).json()["id"]
    transport(monkeypatch, lambda req: httpx.Response(429))
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 503
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"]
    transport(
        monkeypatch,
        lambda req: httpx.Response(
            403, json={"error": {"errors": [{"reason": "rateLimitExceeded"}]}}
        ),
    )
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 503
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"]
    transport(monkeypatch, lambda req: httpx.Response(404))
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").json() == {
        "removed": True
    }
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


def test_old_grant_failure_does_not_disconnect_new_grant(system):
    old = connected(system)
    sources.disconnect(system.factory, "alice", "google_docs")
    new = connected(system)
    assert new != old
    sources.disconnect(system.factory, "alice", "google_docs", expected=old)
    with system.factory() as session:
        assert session.get(SourceConnection, ("alice", "google_docs")).grant_id == new
