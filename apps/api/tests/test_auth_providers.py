import httpx
import pytest
import test_workspaces

from ghosttab_api import auth_providers

system = test_workspaces.system


def test_local_mode_never_requests_an_identity_provider(system, monkeypatch):
    def unexpected(**kwargs):
        raise AssertionError("Local mode must not read Supabase")

    monkeypatch.setattr(auth_providers.httpx, "Client", unexpected)
    assert system.request("GET", "/auth/providers").json() == {"google": "disabled"}


@pytest.mark.parametrize(
    "body,code,expected",
    [
        ({"external": {"google": True}}, 200, "enabled"),
        ({"external": {"google": False}}, 200, "disabled"),
        ({"external": {"google": "true"}}, 200, "unavailable"),
        ({"external": []}, 200, "unavailable"),
        ({"error": "private details"}, 429, "unavailable"),
        ({}, 302, "unavailable"),
    ],
)
def test_status_is_bounded_read_only_and_does_not_expose_provider_payload(
    system, monkeypatch, body, code, expected
):
    system.settings.auth_mode = "supabase"
    system.settings.supabase_url = "https://identity.example.test"
    system.settings.supabase_publishable_key = "synthetic-public-key"
    original = httpx.Client

    def respond(req):
        assert (
            req.method == "GET" and str(req.url) == "https://identity.example.test/auth/v1/settings"
        )
        assert req.headers["apikey"] == "synthetic-public-key"
        return httpx.Response(code, json=body)

    monkeypatch.setattr(
        auth_providers.httpx,
        "Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    result = system.request("GET", "/auth/providers")
    assert result.status_code == 200 and result.json() == {"google": expected}


def test_provider_timeout_does_not_block_email_signup(system, monkeypatch):
    system.settings.auth_mode = "supabase"
    system.settings.supabase_url = "https://identity.example.test"
    original = httpx.Client

    def timeout(req):
        raise httpx.ReadTimeout("private detail")

    monkeypatch.setattr(
        auth_providers.httpx,
        "Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(timeout)),
    )
    assert system.request("GET", "/auth/providers").json() == {"google": "unavailable"}
