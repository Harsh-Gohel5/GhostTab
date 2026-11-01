"""The rehearsal has two owners and deterministic failures, never real accounts."""

import pytest
from auth_browser_fixture import create_auth_fixture
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    # API CI runs independently of the frontend build job.
    app = create_auth_fixture(tmp_path, dist=tmp_path)
    with TestClient(app) as client:
        yield client
    app.state.sessions.kw["bind"].dispose()


def signin(client, email):
    response = client.post(
        "/auth/v1/token?grant_type=password",
        json={"email": email, "password": "demo-password"},
    )
    assert response.status_code == 200
    return response.json()


def test_two_accounts_preserve_private_tasks_across_switch_and_reload(client):
    first = signin(client, "demo@example.test")
    second = signin(client, "other@example.test")
    headers = {"Authorization": "Bearer " + first["access_token"]}
    task = client.post(
        "/api/tasks", headers=headers, json={"title": "A only", "goal": "Private sample"}
    ).json()
    other_headers = {"Authorization": "Bearer " + second["access_token"]}
    assert client.get("/api/tasks", headers=other_headers).json() == []
    assert (
        client.get(f"/api/tasks/{task['id']}/workspace", headers=other_headers).status_code == 404
    )
    refreshed = client.post(
        "/auth/v1/token?grant_type=refresh_token", json={"refresh_token": first["refresh_token"]}
    ).json()
    assert refreshed["user"]["id"] == first["user"]["id"]
    assert client.get("/api/tasks", headers=headers).json()[0]["id"] == task["id"]


def test_failure_controls_are_bounded_and_recoverable(client):
    account = signin(client, "demo@example.test")
    assert client.post("/synthetic/scenario", json={"tasks_delay_ms": 6000}).status_code == 422
    assert client.post("/synthetic/scenario", json={"logout_failure": True}).status_code == 200
    assert client.post("/auth/v1/logout").status_code == 503
    for failure, status in [("rejected", 400), ("temporary", 503)]:
        client.post("/synthetic/scenario", json={"refresh_failure": failure})
        assert (
            client.post(
                "/auth/v1/token?grant_type=refresh_token",
                json={"refresh_token": account["refresh_token"]},
            ).status_code
            == status
        )
    client.post("/synthetic/scenario", json={})
    assert client.post("/auth/v1/logout").status_code == 204
    assert (
        client.post(
            "/auth/v1/token?grant_type=refresh_token", json={"refresh_token": "unknown"}
        ).status_code
        == 400
    )


def test_fixture_preparation_uses_fake_model_for_signed_in_draft_checks(client, monkeypatch):
    from ghosttab_api.meta import MetaClient

    def forbidden(*_):
        pytest.fail("Fixture must never use a live model client")

    monkeypatch.setattr(MetaClient, "complete", forbidden)
    account = signin(client, "demo@example.test")
    headers = {"Authorization": "Bearer " + account["access_token"]}
    task = client.post(
        "/api/tasks", headers=headers, json={"title": "Draft sample", "goal": "Check sign-out"}
    ).json()
    tid = task["id"]
    client.post(
        f"/api/tasks/{tid}/evidence",
        headers=headers,
        json={"title": "Fictional note", "content": "Review the fictional plan."},
    )
    assert client.post(f"/api/tasks/{tid}/prepare", headers=headers).status_code == 202
    snapshot = client.get(f"/api/tasks/{tid}/workspace", headers=headers).json()["snapshot"]
    assert "Synthetic draft" in snapshot["draft"]
