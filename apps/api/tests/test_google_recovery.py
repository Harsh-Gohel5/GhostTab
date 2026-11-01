"""Reconnection must rebuild access explicitly without resurrecting old results."""

import httpx
import test_google_sources
from connector_samples import SampleModel
from fastapi import HTTPException

from ghosttab_api import calendar
from ghosttab_api.models import SourceConnection
from ghosttab_api.worker import run_once

system = test_google_sources.system


def test_docs_transient_failure_revocation_and_explicit_reimport(system, monkeypatch):
    helper = test_google_sources
    helper.connected(system)
    helper.transport(monkeypatch)
    tid = helper.task(system)
    path = f"/tasks/{tid}/imports/google_docs"
    eid = system.request("POST", path, {"item_id": "synthetic_doc"}).json()["id"]
    system.request(
        "POST", f"/tasks/{tid}/evidence", {"title": "Keep notes", "content": "Manual context"}
    )
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    before = system.request("GET", f"/tasks/{tid}/workspace").json()
    helper.transport(monkeypatch, lambda req: httpx.Response(429))
    assert system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh").status_code == 503
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["snapshot"] == before["snapshot"]
    helper.transport(monkeypatch, lambda req: httpx.Response(401))
    system.request("POST", f"/tasks/{tid}/evidence/{eid}/refresh")
    blocked = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert blocked["snapshot"] is None
    assert [x["origin"] for x in blocked["evidence"]] == ["manual"]
    # Resource denial blocks that source; a rejected refresh revokes the grant.
    with system.factory.begin() as session:
        row = session.get(SourceConnection, ("alice", "google_docs"))
        tokens = calendar.decrypt(system.settings, row.encrypted_tokens)
        tokens["expires_at"] = 0
        row.encrypted_tokens = calendar.encrypt(system.settings, tokens)

    def revoked(*_):
        raise HTTPException(401, "Synthetic revoked refresh")

    monkeypatch.setattr(calendar, "token_exchange", revoked)
    assert system.request("POST", path, {"item_id": "synthetic_doc"}).status_code == 401
    helper.connected(system)
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["snapshot"] is None
    helper.transport(monkeypatch)
    reimported = system.request("POST", path, {"item_id": "synthetic_doc"})
    assert reimported.status_code == 200
    assert system.request("GET", f"/tasks/{tid}/workspace").json()["snapshot"] is None
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    after = system.request("GET", f"/tasks/{tid}/workspace").json()
    assert after["task"]["freshness"] == "current"
    assert after["snapshot"]["id"] != before["snapshot"]["id"]
    assert len(after["evidence"]) == 2
