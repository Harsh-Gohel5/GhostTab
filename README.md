# GhostTab

**Your next task, already in context.**

GhostTab prepares workspaces for people whose work spans messages, documents,
meetings, and task tools. It is being built for the Meta Global AI Developer
Hackathon. The goal is to assemble the context for a task, explain what needs
attention, prepare a reviewable next action, and flag context when its sources
change. Developers are one audience alongside marketing, operations, client
services, support, and other knowledge work.

## Current status

This repository contains the first local task/meeting workspace slice:

- Today, Workspaces, and Connections views for a broad knowledge-work audience.
- Persisted tasks, manually added notes, immutable source revisions, and draft editing.
- Google Calendar read-only OAuth adapter, upcoming-event selection and manual refresh.
- A durable worker with bounded Meta requests, citation validation, source-generation
  checks, lease recovery, and a usage/reservation ledger.
- Local development identity and a Supabase JWT/email-password sign-in path.
- SQLAlchemy/Alembic schema for SQLite development and PostgreSQL deployment.
- Frontend type checking and linting, backend linting and tests, and GitHub Actions CI.
- Environment examples, dependency locks, and project architecture notes.

**Live Google authorization and Meta inference are not verified yet.** Provider
adapters have tests with synthetic data and mocked responses. Meta requests are
disabled by default, even if a key is supplied. No paid resource or model call was
created during implementation. See [setup](docs/setup.md).

Google Calendar is the first confirmed connector. Mail, chat, document retrieval,
scheduled synchronization, hosted deployment, and the local Git bridge remain
future work. Calendar events are imported only when selected. **Check Calendar**
is a manual action; no real-time synchronization is claimed.

## Requirements

- Node.js 22.12 or later (Node 22 recommended) and npm.
- Python 3.12 or later (Python 3.13 recommended).
- Git.

No API credentials, Docker installation, hosted database, or paid service is needed
for the local workspace. SQLite is included with Python. Run from the repository root.

## Setup on Windows (PowerShell)

```powershell
npm.cmd ci
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e ./apps/api
Copy-Item .env.example .env
```

The explicit interpreter path avoids changing PowerShell execution policy or
requiring virtual environment activation. The `.env` copy is optional until
configuration changes are needed; do not overwrite an existing `.env`.

Start the backend in one terminal:

```powershell
npm.cmd run db:migrate
npm.cmd run dev:api
```

Start the frontend in another:

```powershell
npm.cmd run dev
```

- Interface: <http://127.0.0.1:5173>
- API health: <http://127.0.0.1:8000/api/health>
- Development API docs: <http://127.0.0.1:8000/api/docs>

Both servers bind to loopback. Stop a server with Ctrl+C. If the API is stopped,
the interface reports it as unavailable and provides a retry action.

## Setup on macOS / Linux

```bash
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-deps -e ./apps/api
# Optional, only if .env does not exist:
cp .env.example .env
```

Run `npm run db:migrate`, then `npm run dev:api` and `npm run dev` in separate terminals. The backend launcher
selects the correct local virtual environment on each operating system.

## Verify changes

```powershell
npm.cmd run check
npm.cmd run build
```

`check` runs TypeScript, ESLint, Ruff lint/format checks, and the API test suite.
The production frontend bundle is generated in `apps/web/dist`. Deployment
and production routing will be configured in a later milestone;
these development commands are not a deployment recipe.

## Repository layout

```text
apps/
  web/                     React / TypeScript / Vite interface
  api/
    src/ghosttab_api/       API, identity, Calendar adapter, storage and worker
    migrations/            Versioned database migrations
    tests/                 Authorization, revision, worker and adapter tests
docs/
  architecture.md          Current state, target design, data model and flows
  roadmap.md               Dated phases, release gates and scope cuts
  model-budget.md          Meta model selection and credit controls
  demo-plan.md             Evaluation, three-minute story and submission
  whiteboard.md            Interview explanation and architecture tradeoffs
  setup.md                 Local setup, cost boundary, Google and Meta configuration
scripts/python.mjs         Cross-platform local backend launcher
.github/workflows/ci.yml    Frontend and backend checks
```

## Configuration

Copy `.env.example` to `.env` when needed. `GHOSTTAB_ENVIRONMENT` accepts
`development`, `test`, or `production`; production disables the API schema and
documentation endpoints. The health endpoint is process liveness, not proof that
connectors or a preparation worker are ready.

See [setup.md](docs/setup.md) for Calendar authorization, Meta credit verification,
and optional hosted identity. Keep credentials out of source files, issues, screenshots, or chat. Browser
variables prefixed with `VITE_` are public, so they must never contain secrets.
The adapter targets `https://api.meta.ai/v1` with `muse-spark-1.3`; account access
remains to be checked. `GHOSTTAB_ALLOW_MODEL_REQUESTS=false` prevents admission
and provider submission. Enable it only after credit/billing verification.

## Product direction

The proposed first connected flow starts from a selected work request, collects
authorized mail/chat/document evidence, uses a Meta model to prepare a grounded
task brief and editable next action, and assembles an inspectable workspace.
A later relevant source change should mark that snapshot stale. Google Calendar
is the first confirmed source; additional mail/chat/document accounts are pending.
Microsoft 365 is an alternative ecosystem; Jira and GitHub can add
project and engineering context after the shared workflow is reliable.

See [architecture](docs/architecture.md), [roadmap](docs/roadmap.md),
[model and budget plan](docs/model-budget.md), [demo plan](docs/demo-plan.md), and
[whiteboard guide](docs/whiteboard.md).

The approved interface uses a light neutral base with indigo actions and teal
highlights. See [design direction](docs/design.md) for palette and interaction guidance.

Measure time to a usable workspace, citation validity, relevant-file selection,
and freshness lag on realistic tasks. Do not treat an inferred reproduction or
suspected cause as a verified result.
