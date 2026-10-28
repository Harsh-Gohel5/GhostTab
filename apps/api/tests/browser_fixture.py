"""Isolated browser QA: real API/UI with synthetic evidence and a fake model.

Run `npm run build`, then `.venv/Scripts/python.exe apps/api/tests/browser_fixture.py`.
Open http://127.0.0.1:8010. No .env, account credentials or live providers are used.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from fastapi.staticfiles import StaticFiles
from test_workspaces import FakeModel

from ghosttab_api.config import Settings
from ghosttab_api.contracts import EvidenceInput
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.main import create_app
from ghosttab_api.models import Base, Budget, Task
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
            google_client_id="",
            google_client_secret="",
            token_encryption_key="",
            frontend_url="http://127.0.0.1:8010",
            database_url=f"sqlite:///{Path(directory).as_posix()}/fixture.db",
            allow_model_requests=True,
            model_api_key="synthetic-fixture-only",
        )
        engine = make_engine(settings.database_url)
        Base.metadata.create_all(engine)
        factory = sessions(engine)
        with factory.begin() as session:
            session.add(Budget(id=1, charged_microusd=0))
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
        app = create_app(settings, engine=engine)

        @app.middleware("http")
        async def fake_preparation(request, call_next):
            response = await call_next(request)
            if request.method == "POST" and request.url.path.endswith("/prepare"):
                # This database belongs only to this fixture process. Never use a live client.
                run_once(factory, settings, FakeModel())
            return response

        app.mount("/", StaticFiles(directory=dist, html=True))
        try:
            with worker_presence(factory):
                uvicorn.run(app, host="127.0.0.1", port=8010, log_level="warning", access_log=False)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
