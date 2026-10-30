import hashlib
import time
from copy import deepcopy
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import test_workspaces
from connector_samples import RESPONSES, SampleModel
from fastapi import HTTPException
from pydantic import SecretStr

from ghosttab_api import calendar, google_sources
from ghosttab_api import jira_sources as jira
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.models import SourceConnection
from ghosttab_api.worker import run_once

system = test_workspaces.system
CLOUD = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"


def tokens(**updates):
    return {
        "access_token": "synthetic-jira",
        "refresh_token": "synthetic-refresh",
        "expires_at": time.time() + 3600,
        "scope": jira.READ_SCOPE,
        "site_ids": [CLOUD],
        **updates,
    }


def connected(system, **updates):
    with system.factory.begin() as session:
        row = SourceConnection(
            owner_id="alice",
            provider="jira",
            encrypted_tokens=calendar.encrypt(system.settings, tokens(**updates)),
        )
        session.add(row)
        session.flush()
        return row.grant_id


def transport(
    monkeypatch,
    *,
    sites=None,
    status="In progress",
    resource_status=200,
    issue_status=200,
    after_read=None,
):
    calls = []
    sites = (
        [
            {
                "id": CLOUD,
                "name": "Fictional Jira",
                "url": "https://demo.atlassian.net",
                "scopes": [jira.READ_SCOPE],
            }
        ]
        if sites is None
        else sites
    )

    def respond(req):
        calls.append(req)
        assert req.method == "GET" and req.headers["Authorization"] == "Bearer synthetic-jira"
        assert req.url.host == "api.atlassian.com"
        if req.url.path.endswith("accessible-resources"):
            return httpx.Response(resource_status, json=sites)
        assert req.url.path.startswith("/ex/jira/")
        body = deepcopy(RESPONSES["api.atlassian.com"])
        body["fields"]["status"]["name"] = status
        if after_read:
            after_read()
        return httpx.Response(issue_status, json=body)

    monkeypatch.setattr(
        jira,
        "client_for",
        lambda token: httpx.Client(
            headers={"Authorization": "Bearer " + token}, transport=httpx.MockTransport(respond)
        ),
    )
    return calls


def task(system):
    return system.request(
        "POST", "/tasks", {"title": "Fictional Jira task", "goal": "Review issue."}
    ).json()["id"]


def selection(cloud=CLOUD):
    return {"cloud_id": cloud, "issue_key": "DEMO-1"}


def test_oauth_browser_owner_binding_scope_and_single_use(system, monkeypatch):
    system.settings.jira_client_id = "synthetic-client"
    system.settings.jira_client_secret = SecretStr("synthetic-secret")
    response = system.request("POST", "/integrations/jira/start")
    query = parse_qs(urlparse(response.json()["url"]).query)
    assert set(query["scope"][0].split()) == {jira.READ_SCOPE, "offline_access"}
    assert query["audience"] == ["api.atlassian.com"]
    state = query["state"][0]
    monkeypatch.setattr(jira, "exchange", lambda *_: tokens())
    transport(monkeypatch)
    with pytest.raises(HTTPException):
        jira.finish(system.factory, system.settings, state, "wrong", "code", "")
    jira.finish(
        system.factory,
        system.settings,
        state,
        hashlib.sha256(state.encode()).hexdigest(),
        "code",
        "",
    )
    with pytest.raises(HTTPException):
        jira.finish(
            system.factory,
            system.settings,
            state,
            hashlib.sha256(state.encode()).hexdigest(),
            "code",
            "",
        )
    with system.factory() as session:
        assert (
            "synthetic-jira"
            not in session.get(SourceConnection, ("alice", "jira")).encrypted_tokens
        )


def test_import_dedup_refresh_citations_disconnect(system, monkeypatch):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    path = f"/tasks/{tid}/imports/jira"
    result = system.request("POST", path, selection())
    assert result.status_code == 200, result.text
    eid = result.json()["id"]
    assert system.request("POST", path, selection()).json()["id"] == eid
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    original = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert original["snapshot"] and original["task"]["source_count"] == 1
    assert original["evidence"][0]["url"] == "https://demo.atlassian.net/browse/DEMO-1"
    transport(monkeypatch, status="Done")
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 200
    updated = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert updated["task"]["freshness"] == "stale" and updated["snapshot"] == original["snapshot"]
    assert system.request("DELETE", "/integrations/jira").status_code == 204
    removed = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert not removed["evidence"] and removed["snapshot"] is None


def test_ungranted_site_and_other_owner_never_read_issue(system, monkeypatch):
    connected(system)
    calls = transport(monkeypatch)
    tid = task(system)
    assert system.request("POST", f"/tasks/{tid}/imports/jira", selection(OTHER)).status_code == 403
    assert len(calls) == 1
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert system.request("POST", f"/tasks/{tid}/imports/jira", selection()).status_code == 404
    assert len(calls) == 1


def test_site_loss_blocks_sources_but_retains_other_site_and_fences_reads(system, monkeypatch):
    connected(system)
    sites = [
        {"id": cloud, "url": f"https://site{index}.atlassian.net", "scopes": [jira.READ_SCOPE]}
        for index, cloud in enumerate((CLOUD, OTHER))
    ]
    transport(monkeypatch, sites=sites)
    tid = task(system)
    first = system.request("POST", f"/tasks/{tid}/imports/jira", selection()).json()["id"]
    second = system.request("POST", f"/tasks/{tid}/imports/jira", selection(OTHER)).json()["id"]
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    old = jira.access(system.factory, system.settings, "alice")[1]
    transport(monkeypatch, sites=sites[1:])
    assert system.request("GET", "/integrations/jira/sites").status_code == 200
    result = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert [e["id"] for e in result["evidence"]] == [second] and result["snapshot"] is None
    assert first != second
    with system.factory.begin() as session:
        with pytest.raises(HTTPException):
            google_sources.grant(session, "alice", "jira", old, lock=True)
    assert system.request("POST", f"/tasks/{tid}/evidence/{second}/refresh").status_code == 200


@pytest.mark.parametrize("code,expected", [(429, 503), (500, 503), (401, 401)])
def test_transient_failure_preserves_sources_revocation_blocks(system, monkeypatch, code, expected):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request("POST", f"/tasks/{tid}/imports/jira", selection()).json()["id"]
    transport(monkeypatch, resource_status=code)
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == expected
    evidence = system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"]
    assert bool(evidence) == (code != 401)


def test_disconnect_during_read_cannot_publish(system, monkeypatch):
    connected(system)
    transport(
        monkeypatch, after_read=lambda: google_sources.disconnect(system.factory, "alice", "jira")
    )
    tid = task(system)
    assert system.request("POST", f"/tasks/{tid}/imports/jira", selection()).status_code == 409
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["evidence"] == []


@pytest.mark.parametrize("code", [401, 403, 404])
def test_issue_access_loss_blocks_saved_context(system, monkeypatch, code):
    connected(system)
    transport(monkeypatch)
    tid = task(system)
    eid = system.request("POST", f"/tasks/{tid}/imports/jira", selection()).json()["id"]
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    transport(monkeypatch, issue_status=code)
    result = system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh")
    assert result.status_code == (401 if code == 401 else 200)
    result = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert result["evidence"] == [] and result["snapshot"] is None


def test_malformed_site_response_preserves_saved_grant(system, monkeypatch):
    connected(system)
    transport(
        monkeypatch, sites=[{"id": CLOUD, "url": "https://evil.test", "scopes": [jira.READ_SCOPE]}]
    )
    assert system.request("GET", "/integrations/jira/sites").status_code == 502
    assert system.request("GET", "/integrations/jira").json()["connected"]


def test_rotating_token_preserves_sites(system, monkeypatch):
    connected(system, expires_at=time.time() - 1)
    monkeypatch.setattr(
        jira, "exchange", lambda *_: tokens(refresh_token="rotated", scope="", site_ids=[])
    )
    value, _ = jira.access(system.factory, system.settings, "alice")
    assert value["site_ids"] == [CLOUD] and value["refresh_token"] == "rotated"


@pytest.mark.parametrize(
    "url",
    [
        "http://demo.atlassian.net",
        "https://evil.test",
        "https://user@demo.atlassian.net",
        "https://demo.atlassian.net/path",
    ],
)
def test_untrusted_site_urls_are_rejected(url):
    with pytest.raises(ValueError):
        jira.site_origin(url)


def test_exchange_requires_complete_rotating_grant(system, monkeypatch):
    original = httpx.Client
    body = {
        "access_token": "synthetic",
        "refresh_token": "synthetic-refresh",
        "expires_in": 3600,
        "scope": jira.READ_SCOPE,
    }
    monkeypatch.setattr(
        jira.httpx,
        "Client",
        lambda **kwargs: original(
            **kwargs, transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
        ),
    )
    assert (
        jira.exchange(system.settings, {"code": "synthetic"})["refresh_token"]
        == "synthetic-refresh"
    )
    del body["refresh_token"]
    with pytest.raises(HTTPException):
        jira.exchange(system.settings, {"code": "synthetic"})
