"""Isolated browser QA: real API/UI with synthetic evidence and a fake model.

Run `npm run build`, then `.venv/Scripts/python.exe apps/api/tests/browser_fixture.py`.
Open http://127.0.0.1:8010. No .env, account credentials or live providers are used.
"""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import uvicorn
from connector_samples import RESPONSES, SampleModel, sample_sources
from cryptography.fernet import Fernet
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ghosttab_api import calendar, google_sources, jira_sources, slack_sources, teams_sources
from ghosttab_api.config import Settings
from ghosttab_api.contracts import EvidenceInput
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.main import create_app
from ghosttab_api.models import Base, Budget, SourceConnection, Task
from ghosttab_api.readiness import worker_presence
from ghosttab_api.worker import run_once
from ghosttab_api.workspaces import put_evidence


def main():
    dist = Path(__file__).resolve().parents[3] / "apps/web/dist"
    if not dist.is_dir():
        raise SystemExit("Run npm run build first.")
    with TemporaryDirectory(prefix="ghosttab-browser-qa-") as directory:
        settings = Settings(
            _env_file=None,
            environment="test",
            auth_mode="local",
            supabase_url="",
            supabase_publishable_key="",
            google_client_id="synthetic-client",
            google_client_secret="synthetic-secret",
            jira_client_id="synthetic-jira-client",
            teams_client_id="synthetic-teams-client",
            teams_client_secret="synthetic-teams-secret",
            teams_tenant_id="11111111-1111-4111-8111-111111111111",
            jira_client_secret="synthetic-jira-secret",
            slack_client_id="synthetic-slack-client",
            slack_client_secret="synthetic-slack-secret",
            token_encryption_key=Fernet.generate_key().decode(),
            frontend_url="http://127.0.0.1:8010",
            database_url=f"sqlite:///{Path(directory).as_posix()}/fixture.db",
            allow_model_requests=True,
            model_api_key="synthetic-fixture-only",
            synthetic_demo=True,
        )
        engine = make_engine(settings.database_url)
        Base.metadata.create_all(engine)
        factory = sessions(engine)
        with factory.begin() as session:
            session.add(Budget(id=1, charged_microusd=0))
            session.add(
                SourceConnection(
                    owner_id="local-owner",
                    provider="teams",
                    encrypted_tokens=calendar.encrypt(
                        settings,
                        {
                            "access_token": "synthetic-teams",
                            "refresh_token": "synthetic-refresh",
                            "expires_at": time.time() + 86400,
                            "scope": "Chat.Read",
                            "tenant_id": settings.teams_tenant_id,
                        },
                    ),
                )
            )
            session.add(
                SourceConnection(
                    owner_id="local-owner",
                    provider="slack",
                    encrypted_tokens=calendar.encrypt(
                        settings,
                        {
                            "access_token": "synthetic-slack",
                            "refresh_token": "",
                            "expires_at": None,
                            "scope": "channels:read,channels:history",
                            "team_id": "TDEMO123",
                        },
                    ),
                )
            )
            session.add(
                SourceConnection(
                    owner_id="local-owner",
                    provider="jira",
                    encrypted_tokens=calendar.encrypt(
                        settings,
                        {
                            "access_token": "synthetic-jira",
                            "refresh_token": "synthetic-refresh",
                            "expires_at": time.time() + 86400,
                            "scope": "read:jira-work",
                            "site_ids": ["11111111-1111-4111-8111-111111111111"],
                        },
                    ),
                )
            )
            for provider, scope in google_sources.SCOPES.items():
                session.add(
                    SourceConnection(
                        owner_id="local-owner",
                        provider=provider,
                        encrypted_tokens=calendar.encrypt(
                            settings,
                            {
                                "access_token": "synthetic-access",
                                "refresh_token": "synthetic-refresh",
                                "scope": scope,
                                "expires_at": time.time() + 86400,
                            },
                        ),
                    )
                )
            task = Task(
                owner_id="local-owner",
                title="QA fixture: draft safety",
                goal="Synthetic browser test. Briefs use a fake model; nothing is sent to Meta.",
            )
            session.add(task)
            session.flush()
            put_evidence(
                session,
                task,
                EvidenceInput(
                    title="Fictional launch request", content="Review the launch plan on Thursday."
                ),
            )
            for item in sample_sources():
                put_evidence(session, task, item.evidence, origin="sample_" + item.provider)
        app = create_app(settings, engine=engine)

        def respond(req):
            if req.url.host == "graph.microsoft.com" and not req.url.path.endswith("/messages"):
                return httpx.Response(
                    200,
                    json={
                        "id": "19:synthetic@thread.v2",
                        "chatType": "group",
                        "topic": "Fictional handoff chat",
                    },
                )
            if req.url.path.endswith("accessible-resources"):
                return httpx.Response(
                    200,
                    json=[
                        {
                            "id": "11111111-1111-4111-8111-111111111111",
                            "name": "Fictional Jira",
                            "url": "https://demo.atlassian.net",
                            "scopes": ["read:jira-work"],
                        }
                    ],
                )
            if req.url.host == "slack.com" and req.url.path.endswith("conversations.info"):
                return httpx.Response(
                    200,
                    json={
                        "ok": True,
                        "channel": {"id": "CDEMO123", "name": "demo-launch", "is_private": False},
                    },
                )
            if req.url.host == "gmail.googleapis.com" and req.url.path.endswith("/messages"):
                return httpx.Response(200, json={"messages": [{"id": "aabbcc"}]})
            return httpx.Response(200, json=RESPONSES[req.url.host])

        google_sources.client_for = lambda token: httpx.Client(
            transport=httpx.MockTransport(respond)
        )
        slack_sources.client_for = lambda token: httpx.Client(
            transport=httpx.MockTransport(respond)
        )

        jira_sources.client_for = lambda token: httpx.Client(transport=httpx.MockTransport(respond))
        teams_sources.client_for = lambda token: httpx.Client(
            transport=httpx.MockTransport(respond)
        )

        @app.middleware("http")
        async def fake_preparation(request, call_next):
            if request.url.path.endswith("/start"):
                return JSONResponse(
                    {"detail": "Authorization is disabled in the synthetic test app."},
                    status_code=503,
                )
            response = await call_next(request)
            if request.method == "POST" and request.url.path.endswith("/prepare"):
                # This database belongs only to this fixture process. Never use a live client.
                run_once(factory, settings, SampleModel())
            return response

        app.mount("/", StaticFiles(directory=dist, html=True))
        try:
            with worker_presence(factory):
                uvicorn.run(app, host="127.0.0.1", port=8010, log_level="warning", access_log=False)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
