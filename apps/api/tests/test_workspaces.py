import asyncio
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

import httpx
import jwt
import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select, text

from ghosttab_api import calendar
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.main import create_app
from ghosttab_api.meta import MetaClient, ModelFailure, ModelResult
from ghosttab_api.models import Base, Budget, Connection, Job, ModelRun, OAuthState
from ghosttab_api.worker import claim_job, run_once


@pytest.fixture
def system(tmp_path):
    url = os.environ.get("GHOSTTAB_TEST_DATABASE_URL")
    admin = None
    if url:
        # A unique schema prevents a test run from touching existing application tables.
        admin = create_engine(url)
        schema = "test_" + uuid4().hex
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = make_engine(url).execution_options(schema_translate_map={None: schema})
    else:
        engine = make_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessions(engine)
    with factory.begin() as session:
        session.add(Budget(id=1, charged_microusd=0))
    settings = Settings(
        environment="test",
        _env_file=None,
        model_api_key="test-key",
        allow_model_requests=True,
        google_client_id="test-client",
        google_client_secret="test-secret",
        token_encryption_key=Fernet.generate_key().decode(),
    )
    app = create_app(settings, engine=engine)
    app.dependency_overrides[current_user] = lambda: Principal("alice")

    def request(method, path, body=None):
        async def send():
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                return await client.request(method, "/api" + path, json=body)

        return asyncio.run(send())

    yield SimpleNamespace(
        app=app, settings=settings, factory=factory, request=request, engine=engine
    )
    engine.dispose()
    if admin:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def seeded(system):
    task = system.request(
        "POST",
        "/tasks",
        {"title": "Client planning meeting", "goal": "Prepare the decisions and questions"},
    ).json()
    evidence = system.request(
        "POST",
        f"/tasks/{task['id']}/evidence",
        {
            "title": "Meeting request",
            "content": "Review the launch plan on Thursday.",
            "url": "https://example.com/meeting",
        },
    ).json()
    return task["id"], evidence["id"]


class FakeModel:
    def __init__(self, *, mutate=None, bad_quote=False):
        self.mutate = mutate
        self.bad_quote = bad_quote
        self.calls = 0

    def complete(self, body):
        self.calls += 1
        source = json.loads(body["messages"][1]["content"])["evidence"][0]
        point = {
            "text": "Review the launch plan.",
            "citations": [
                {
                    "evidence_id": source["id"],
                    "quote": "not present in source" if self.bad_quote else source["content"],
                }
            ],
        }
        if self.mutate:
            self.mutate()
        return ModelResult(
            json.dumps(
                {
                    "summary": point,
                    "facts": [point],
                    "next_steps": [point],
                    "unknowns": ["Approval owner is unknown."],
                    "draft": "Could you confirm who will approve the plan?",
                }
            ),
            {"prompt_tokens": 800, "completion_tokens": 200},
            "test-request",
        )


def test_preparation_is_durable_deduplicated_and_editable(system):
    task, _ = seeded(system)
    first = system.request("POST", f"/tasks/{task}/prepare")
    second = system.request("POST", f"/tasks/{task}/prepare")
    assert first.status_code == 202 and first.json()["id"] == second.json()["id"]
    model = FakeModel()
    # New session factory represents a restarted worker reading the saved queue.
    assert run_once(sessions(system.engine), system.settings, model)
    assert not run_once(system.factory, system.settings, model)
    assert model.calls == 1
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["task"]["freshness"] == "current"
    assert data["task"]["job"]["status"] == "succeeded"
    assert data["snapshot"]["citations"][0]["content"] == "Review the launch plan on Thursday."
    snapshot = data["snapshot"]["id"]
    assert (
        system.request(
            "PUT", f"/tasks/{task}/draft?snapshot_id={snapshot}", {"draft": "My reviewed draft"}
        ).status_code
        == 200
    )
    assert (
        system.request("GET", f"/tasks/{task}/workspace").json()["snapshot"]["draft"]
        == "My reviewed draft"
    )
    with system.factory() as session:
        run = session.scalar(select(ModelRun))
        assert run.status == "validated" and run.cost_microusd == 1850
        assert session.get(Budget, 1).charged_microusd == 1850


def test_ownership_is_checked_on_every_resource(system):
    task, evidence = seeded(system)
    job = system.request("POST", f"/tasks/{task}/prepare").json()["id"]
    run_once(system.factory, system.settings, FakeModel())
    snapshot = system.request("GET", f"/tasks/{task}/workspace").json()["snapshot"]["id"]
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert system.request("GET", "/tasks").json() == []
    for method, path, body in [
        ("GET", f"/tasks/{task}/workspace", None),
        ("GET", f"/jobs/{job}", None),
        ("POST", f"/tasks/{task}/prepare", None),
        ("POST", f"/tasks/{task}/evidence", {"title": "x", "content": "x"}),
        ("PUT", f"/tasks/{task}/evidence/{evidence}", {"title": "x", "content": "x"}),
        ("DELETE", f"/tasks/{task}/evidence/{evidence}", None),
        ("PUT", f"/tasks/{task}/draft?snapshot_id={snapshot}", {"draft": "stolen"}),
        ("POST", f"/tasks/{task}/sync", None),
    ]:
        assert system.request(method, path, body).status_code == 404, path


def test_changed_evidence_keeps_the_cited_revision_then_refreshes(system):
    task, evidence = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    run_once(system.factory, system.settings, FakeModel())
    system.request(
        "PUT",
        f"/tasks/{task}/evidence/{evidence}",
        {"title": "Meeting request", "content": "Review the launch plan on Friday."},
    )
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["task"]["freshness"] == "stale"
    assert "Thursday" in data["snapshot"]["citations"][0]["content"]
    assert "Friday" in data["evidence"][0]["content"]
    system.request("POST", f"/tasks/{task}/prepare")
    run_once(system.factory, system.settings, FakeModel())
    assert (
        system.request("GET", f"/tasks/{task}/workspace").json()["task"]["freshness"] == "current"
    )


def test_removed_source_blocks_derived_brief(system):
    task, evidence = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    run_once(system.factory, system.settings, FakeModel())
    system.request("DELETE", f"/tasks/{task}/evidence/{evidence}")
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["snapshot"] is None and data["evidence"] == []


def test_readiness_metadata_counts_only_active_owned_sources(system):
    empty = system.request("POST", "/tasks", {"title": "Same meeting", "goal": "Prepare"}).json()
    assert empty["source_count"] == 0
    assert empty["calendar_event_id"] is None
    task, evidence = seeded(system)
    item = next(x for x in system.request("GET", "/tasks").json() if x["id"] == task)
    assert item["source_count"] == 1
    system.request("DELETE", f"/tasks/{task}/evidence/{evidence}")
    item = next(x for x in system.request("GET", "/tasks").json() if x["id"] == task)
    assert item["source_count"] == 0
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert system.request("GET", "/tasks").json() == []


def test_input_change_during_inference_cannot_publish_old_result(system):
    task, evidence = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    run_once(
        system.factory,
        system.settings,
        FakeModel(
            mutate=lambda: system.request(
                "PUT",
                f"/tasks/{task}/evidence/{evidence}",
                {"title": "Updated", "content": "New decisions"},
            )
        ),
    )
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["snapshot"] is None and data["task"]["job"]["status"] == "superseded"


def test_invalid_citation_fails_without_ready_snapshot_and_accounts_usage(system):
    task, _ = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    run_once(system.factory, system.settings, FakeModel(bad_quote=True))
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["snapshot"] is None
    assert data["task"]["job"]["error_code"] == "invalid_citation"
    with system.factory() as session:
        assert session.get(Budget, 1).charged_microusd == 1850


def test_budget_stops_call_before_provider_submission(system):
    task, _ = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    model = FakeModel()
    run_once(system.factory, system.settings.model_copy(update={"model_budget_usd": 0}), model)
    assert model.calls == 0
    assert (
        system.request("GET", f"/tasks/{task}/workspace").json()["task"]["job"]["error_code"]
        == "budget_exhausted"
    )


def test_model_requests_are_off_by_default_and_disabled_worker_does_not_call(system):
    assert not Settings(_env_file=None).allow_model_requests
    task, _ = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    system.app.state.settings = system.settings.model_copy(update={"allow_model_requests": False})
    assert system.request("POST", f"/tasks/{task}/prepare").status_code == 503
    model = FakeModel()
    run_once(system.factory, system.app.state.settings, model)
    assert model.calls == 0


def test_expired_lease_is_reclaimed_but_attempts_are_bounded(system):
    task, _ = seeded(system)
    job_id = system.request("POST", f"/tasks/{task}/prepare").json()["id"]
    first = claim_job(system.factory)
    assert first and claim_job(system.factory) is None
    with system.factory.begin() as session:
        session.get(Job, job_id).lease_until = 0
    assert claim_job(system.factory)[1] != first[1]
    with system.factory.begin() as session:
        job = session.get(Job, job_id)
        job.attempts = 3
        job.lease_until = 0
    assert claim_job(system.factory) is None
    assert system.request("GET", f"/jobs/{job_id}").json()["status"] == "failed"


def test_concurrent_claims_return_only_one_lease(system):
    task, _ = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim_job(system.factory), range(2)))
    assert sum(x is not None for x in results) == 1


def test_local_identity_rejects_remote_or_cross_origin_requests(system):
    system.app.dependency_overrides.clear()

    async def check():
        async with AsyncClient(
            transport=ASGITransport(app=system.app), base_url="http://test"
        ) as client:
            assert (await client.get("/api/tasks")).status_code == 401
            assert (
                await client.get("/api/tasks", headers={"X-GhostTab-Local": "1"})
            ).status_code == 200
            assert (
                await client.get(
                    "/api/tasks",
                    headers={"X-GhostTab-Local": "1", "Origin": "https://evil.example"},
                )
            ).status_code == 401
        async with AsyncClient(
            transport=ASGITransport(app=system.app, client=("203.0.113.10", 10)),
            base_url="http://test",
        ) as client:
            assert (
                await client.get("/api/tasks", headers={"X-GhostTab-Local": "1"})
            ).status_code == 401

    asyncio.run(check())


def test_jwt_checks_signature_issuer_audience_and_expiration(system):
    system.app.dependency_overrides.clear()
    system.app.state.settings = system.settings.model_copy(
        update={"auth_mode": "supabase", "supabase_url": "https://example.supabase.co"}
    )
    private = ec.generate_private_key(ec.SECP256R1())
    system.app.state.jwks = SimpleNamespace(
        get_signing_key_from_jwt=lambda _: SimpleNamespace(key=private.public_key())
    )
    claims = {
        "sub": "alice",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": "https://example.supabase.co/auth/v1",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
    }

    async def check():
        async with AsyncClient(
            transport=ASGITransport(app=system.app), base_url="http://test"
        ) as client:
            for changes, expected in [
                ({}, 200),
                ({"aud": "wrong"}, 401),
                ({"iss": "wrong"}, 401),
                ({"exp": int(time.time()) - 1}, 401),
                ({"role": "service_role"}, 401),
            ]:
                token = jwt.encode({**claims, **changes}, private, algorithm="ES256")
                assert (
                    await client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})
                ).status_code == expected

    asyncio.run(check())


def test_oauth_state_is_browser_bound_encrypted_and_single_use(system, monkeypatch):
    response = system.request("POST", "/connections/google/start")
    assert response.status_code == 200
    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(response.json()["url"]).query)
    state = query["state"][0]
    digest = hashlib.sha256(state.encode()).hexdigest()
    with system.factory() as session:
        pending = session.get(OAuthState, digest)
        assert state not in pending.encrypted_verifier
        assert query["scope"] == [calendar.SCOPE]
    with pytest.raises(HTTPException):
        calendar.finish_connection(system.factory, system.settings, state, "bad-cookie", "code", "")
    monkeypatch.setattr(
        calendar,
        "token_exchange",
        lambda *_: {
            "access_token": "private-access",
            "refresh_token": "private-refresh",
            "expires_at": time.time() + 3600,
            "scope": calendar.SCOPE,
        },
    )
    calendar.finish_connection(system.factory, system.settings, state, digest, "code", "")
    with system.factory() as session:
        value = session.get(Connection, "alice").encrypted_tokens
        assert "private-access" not in value and "private-refresh" not in value
    with pytest.raises(HTTPException):
        calendar.finish_connection(system.factory, system.settings, state, digest, "code", "")


def test_calendar_selection_sync_and_disconnect_block_derived_content(system, monkeypatch):
    with system.factory.begin() as session:
        session.add(Connection(owner_id="alice", grant_id="grant", encrypted_tokens="encrypted"))
    event = {
        "id": "event1",
        "summary": "Client planning",
        "description": "<p>Review launch plan.</p>",
        "start": {"dateTime": "2026-10-28T09:00:00-07:00"},
        "htmlLink": "https://calendar.google.com/calendar/event?eid=test",
    }
    monkeypatch.setattr(calendar, "calendar_request", lambda *_: (event, "grant"))
    result = system.request("POST", "/tasks/from-calendar", {"event_id": "event1"})
    assert result.status_code == 201
    assert result.json()["calendar_event_id"] == "event1"
    assert result.json()["source_count"] == 1
    task = result.json()["id"]
    assert (
        system.request("POST", "/tasks/from-calendar", {"event_id": "event1"}).json()["id"] == task
    )
    system.request("POST", f"/tasks/{task}/prepare")
    run_once(system.factory, system.settings, FakeModel())
    event["description"] = "Updated agenda: review budget."
    assert system.request("POST", f"/tasks/{task}/sync").status_code == 200
    assert system.request("GET", f"/tasks/{task}/workspace").json()["task"]["freshness"] == "stale"
    assert system.request("DELETE", "/connections/google").status_code == 204
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["snapshot"] is None and data["evidence"] == []
    assert data["task"]["title"] == "Disconnected meeting"
    assert data["task"]["calendar_event_id"] is None
    assert data["task"]["source_count"] == 0


def test_calendar_refresh_preserves_offline_token(system, monkeypatch):
    tokens = {
        "access_token": "old",
        "refresh_token": "keep-me",
        "expires_at": 0,
        "scope": calendar.SCOPE,
    }
    with system.factory.begin() as session:
        session.add(
            Connection(owner_id="alice", encrypted_tokens=calendar.encrypt(system.settings, tokens))
        )
    monkeypatch.setattr(
        calendar,
        "token_exchange",
        lambda *_: {
            "access_token": "new",
            "refresh_token": "",
            "scope": "",
            "expires_at": time.time() + 3600,
        },
    )
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(200, json={"items": []})

    original = httpx.Client
    monkeypatch.setattr(
        calendar.httpx,
        "Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    data, _ = calendar.calendar_request(system.factory, system.settings, "alice")
    assert data == {"items": []}
    assert seen[0].headers["Authorization"] == "Bearer new"
    assert seen[0].url.params["maxResults"] == "25"
    with system.factory() as session:
        assert (
            calendar.decrypt(system.settings, session.get(Connection, "alice").encrypted_tokens)[
                "refresh_token"
            ]
            == "keep-me"
        )


def test_meta_adapter_contract_without_real_network(system, monkeypatch):
    seen = []

    def respond(request):
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "id": "req",
                "choices": [{"finish_reason": "stop", "message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    original = httpx.Client
    monkeypatch.setattr(
        "ghosttab_api.meta.httpx.Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    result = MetaClient(system.settings).complete({"model": "muse-spark-1.3"})
    assert result.request_id == "req"
    assert str(seen[0].url) == "https://api.meta.ai/v1/chat/completions"
    assert seen[0].headers["Authorization"] == "Bearer test-key"


def test_transient_model_failures_keep_reservation_and_do_not_retry_immediately(system):
    task, _ = seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")

    class FailingModel:
        def complete(self, _):
            raise ModelFailure("model_connection_failed", retryable=True)

    run_once(system.factory, system.settings, FailingModel())
    assert not run_once(system.factory, system.settings, FailingModel())
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["task"]["job"]["status"] == "queued"
    with system.factory() as session:
        assert session.get(Budget, 1).charged_microusd > 0


def test_unsafe_source_link_is_rejected(system):
    task, _ = seeded(system)
    assert (
        system.request(
            "POST",
            f"/tasks/{task}/evidence",
            {"title": "Unsafe", "content": "some context", "url": "javascript:alert(1)"},
        ).status_code
        == 422
    )
