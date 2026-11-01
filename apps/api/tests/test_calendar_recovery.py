"""Failures from an old Calendar request must not revoke replacement access."""

import time

import httpx
import pytest
import test_workspaces
from fastapi import HTTPException

from ghosttab_api import calendar
from ghosttab_api.contracts import EvidenceInput
from ghosttab_api.models import Connection, Task
from ghosttab_api.workspaces import put_evidence

system = test_workspaces.system


@pytest.mark.parametrize("failure", ["refresh", "read"])
def test_old_calendar_failure_preserves_replacement_grant_and_evidence(
    system, monkeypatch, failure
):
    def connect(grant, expired=False):
        with system.factory.begin() as session:
            session.merge(
                Connection(
                    owner_id="alice",
                    grant_id=grant,
                    encrypted_tokens=calendar.encrypt(
                        system.settings,
                        {
                            "access_token": "synthetic",
                            "refresh_token": "refresh",
                            "scope": calendar.SCOPE,
                            "expires_at": 0 if expired else time.time() + 3600,
                        },
                    ),
                )
            )

    connect("old", expired=failure == "refresh")
    imported = []

    def replace():
        calendar.disconnect(system.factory, "alice")
        connect("replacement")
        with system.factory.begin() as session:
            task = Task(
                owner_id="alice",
                title="Reconnected",
                goal="Keep new context",
                calendar_event_id="new-event",
            )
            session.add(task)
            session.flush()
            put_evidence(
                session,
                task,
                EvidenceInput(title="New event", content="New grant context"),
                origin="google_calendar",
            )
            imported.append(task.id)

    if failure == "refresh":

        def refresh(*_):
            replace()
            raise HTTPException(401, "Old grant rejected")

        monkeypatch.setattr(calendar, "token_exchange", refresh)
    else:

        def respond(request):
            replace()
            return httpx.Response(401)

        original = httpx.Client
        monkeypatch.setattr(
            calendar.httpx,
            "Client",
            lambda **kw: original(**kw, transport=httpx.MockTransport(respond)),
        )

    with pytest.raises(HTTPException):
        calendar.calendar_request(system.factory, system.settings, "alice")
    with system.factory() as session:
        row = session.get(Connection, "alice")
        assert row is not None and row.grant_id == "replacement"
    workspace = system.request("GET", f"/tasks/{imported[0]}/workspace").json()
    assert workspace["task"]["calendar_event_id"] == "new-event"
    assert len(workspace["evidence"]) == 1
