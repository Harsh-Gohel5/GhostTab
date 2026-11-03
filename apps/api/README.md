# API and preparation worker

FastAPI service with SQLAlchemy persistence and a separate durable worker.
Python 3.12+ is required. Run commands from the repository root; installation and
environment details are in the [setup guide](../../docs/guides/setup.md).

| Area | Modules in `src/ghosttab_api/` |
| --- | --- |
| Application entry | `main.py`, `config.py` |
| Identity and ownership | `auth.py`, `auth_providers.py` |
| Routes and contracts | `routes.py`, `contracts.py` |
| Task evidence and source changes | `workspaces.py`, `source_changes.py` |
| Storage | `database.py`, `models.py` |
| Provider adapters | `calendar.py`, `google_sources.py`, `slack_sources.py`, `jira_sources.py`, `teams_sources.py`, `connector_adapters.py` |
| Preparation | `worker.py`, `meta.py`, `readiness.py` |

`migrations/` holds Alembic versions. `tests/` contains isolated API regressions,
mock providers, model-evaluation runners and disposable browser fixtures.

```sh
npm run dev:api
npm run check:api
npm run db:migrate
```

Start `npm run dev:worker` only when model use and its budget are authorized.
Identity credentials and source grants are separate. Local SQLite data and
encrypted source grants are ignored and must survive repository cleanup.

See [architecture](../../docs/architecture.md),
[connector development](../../docs/connectors/development.md) and
[model budget](../../docs/model-budget.md).
