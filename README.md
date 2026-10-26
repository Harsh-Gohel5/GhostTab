# GhostTab

**Your next task, already in context.**

GhostTab is a developer workspace preparation project for the Meta Global AI
Developer Hackathon. The goal is to assemble the conversation, relevant code,
documentation, and commit evidence for a task, and flag that context when its
sources change.

## Current status

This repository contains the initial development foundation:

- React + TypeScript interface with an honest empty workspace state.
- FastAPI backend with a typed health endpoint and development API docs.
- A live frontend-to-backend health check through Vite's local proxy.
- Frontend type checking and linting, backend linting and tests, and GitHub Actions CI.
- Environment examples, dependency locks, and project architecture notes.

GitHub ingestion, Meta model calls, workspace preparation, persistence, background
refresh, and the local Git bridge are **not implemented yet**. Connecting this
repository to GitHub does not connect the GhostTab application to GitHub.

## Requirements

- Node.js 22.12 or later (Node 22 recommended) and npm.
- Python 3.12 or later (Python 3.13 recommended).
- Git.

No API credentials, database, Docker installation, or paid service is needed to
run the foundation. Run commands from the repository root.

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

Use `npm run dev:api` and `npm run dev` in separate terminals. The backend launcher
selects the correct local virtual environment on each operating system.

## Verify changes

```powershell
npm.cmd run check
npm.cmd run build
```

`check` runs TypeScript, ESLint, Ruff lint/format checks, and the API test suite.
The production frontend bundle is generated in `apps/web/dist`. Deployment,
authentication, and production routing will be configured in a later milestone;
these development commands are not a deployment recipe.

## Repository layout

```text
apps/
  web/                     React / TypeScript / Vite interface
  api/
    src/ghosttab_api/       FastAPI application and settings
    tests/                 API and environment behavior tests
docs/
  architecture.md          Component boundaries and initial decisions
  roadmap.md               MVP milestones and completion criteria
scripts/python.mjs         Cross-platform local backend launcher
.github/workflows/ci.yml    Frontend and backend checks
```

## Configuration

Copy `.env.example` to `.env` when needed. `GHOSTTAB_ENVIRONMENT` accepts
`development`, `test`, or `production`; production disables the API schema and
documentation endpoints. The health endpoint is process liveness, not proof that
connectors or a preparation worker are ready.

GitHub and Meta variables are commented placeholders for upcoming integrations.
Do not add credentials to source files, issues, screenshots, or chat. Browser
variables prefixed with `VITE_` are public, so they must never contain secrets.
The exact Meta endpoint and model will be chosen after verifying granted access.

## Product direction

The first connected flow will start from a selected GitHub issue, collect
commit-pinned evidence, use a Meta model to prepare a grounded task brief, and
assemble an inspectable workspace. A later relevant source change should mark
that snapshot stale. One messaging integration follows the first GitHub flow.

See [architecture](docs/architecture.md) and [roadmap](docs/roadmap.md).

Measure time to a usable workspace, citation validity, relevant-file selection,
and freshness lag on realistic tasks. Do not treat an inferred reproduction or
suspected cause as a verified result.
