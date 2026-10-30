# GhostTab

**Your next task, already in context.**

GhostTab prepares workspaces for people whose work spans messages, documents,
meetings, and task tools. It is being built for the Meta Global AI Developer
Hackathon. The goal is to assemble the context for a task, explain what needs
attention, prepare a reviewable next action, and flag context when its sources
change. Developers are one audience alongside marketing, operations, client
services, support, and other knowledge work.

## Current status

Google identity sign-in is included in the account UI; live Supabase/Google setup
is still pending. Slack's public-thread OAuth/import/refresh/disconnect flow is
implemented and mock-tested, with live installation deferred. See
[Slack setup and limits](docs/slack-source.md). Jira now has a read-only OAuth/site/issue import, refresh and disconnect flow;
live consent remains deferred. See [Jira setup and limits](docs/jira-source.md).
Teams remains a reader adapter without production connection/import UI.

Email sign-up/sign-in/confirmation/recovery UI now uses the existing Supabase path;
live provider setup and email delivery remain pending. See
[account access](docs/account-access.md). Ghosts greet once with a blink/smile on
load and theme changes, respecting reduced-motion settings. A bounded two-case
[Wonder comparison](docs/model-comparison.md) did not show a clear benefit over
Spark for the tested cases, so the default remains Spark.

October 29 checkpoint: persistent light/dark themes, a friendlier SVG ghost with
a subtle dark-mode Halloween accent, and profile initials replace the local
workspace label. Signed-in names come from account metadata/email; local mode
uses the device account name. Five controlled real Meta trials passed schema/quote
validation and scenario-specific agent review; see
[evaluation results and limits](docs/meta-evaluation.md).

This repository contains the first local task/meeting workspace slice:

- Today, Workspaces, and Connections views for a broad knowledge-work audience.
- Persisted tasks, manually added notes, immutable source revisions, and draft editing.
- Human review, completion and reopening, with separate saved-source readiness.
- Google Calendar read-only OAuth adapter, upcoming-event selection and manual refresh.
- A durable worker with bounded Meta requests, citation validation, source-generation
  checks, lease recovery, and a usage/reservation ledger.
- Local development identity and a Supabase JWT/email-password sign-in path.
- SQLAlchemy/Alembic schema for SQLite development and PostgreSQL deployment.
- Frontend type checking and linting, backend linting and tests, and GitHub Actions CI.
- Environment examples, dependency locks, and project architecture notes.

**Live Google authorization and controlled Meta preparation are verified locally.**
Calendar reads/imports and manual refresh work. Synthetic briefs have passed the
worker, schema/citation checks and app-button flow. Provider tests still use mocked
responses. Meta requests are disabled by default; the owner's ignored local setup
is enabled with a $1 cumulative application budget. That estimate-based budget is
not a provider billing guarantee. Credit expiry and overage behavior remain
unconfirmed. See [setup](docs/setup.md).

Google Calendar is the first live-verified connector. Docs/Gmail connection,
selection, import, manual refresh and disconnect flows are implemented and tested
with simulated providers; live authorization is deferred. See
[Google source setup and verification boundaries](docs/google-sources.md).
Live chat verification, scheduled synchronization, hosted deployment, and the local Git
bridge remain future work. Calendar events are imported only when selected. **Check Calendar**
is a manual action; no real-time synchronization is claimed.

Selected-item reader adapters for Docs, Gmail, Slack, Jira and Teams are tested
with synthetic responses. Jira has selected-issue connection/import routes and UI; Teams still has no
production import routes or authorization UI. The isolated browser fixture demonstrates their shared evidence
workflow with explicit sample labels. See [connector development](docs/connector-development.md)
for implemented boundaries and the remaining authorization work.

Today shows saved workspace readiness and links upcoming Calendar events to their
workspace by event ID. Filter Needs attention, Ready to review, or All, then open
the next action. Readiness reflects saved sources, not continuous Calendar polling
or proof that an AI-generated brief is correct.

Saved workspaces support copying the current draft and downloading a Markdown
brief with source quotes. Neither action sends messages or starts inference.
The Workspaces list supports case-insensitive search across titles and goals and
readiness filters with counts. Search words can appear in either field; all words
must match. Filtering uses saved context, performs no model requests or provider
reads, and covers the latest 100 loaded workspaces, not source contents. Search
and filters reset when leaving the list. The default Active filter excludes
completed workspaces; All and Completed keep them accessible. A review applies
to the current saved brief and draft. Source updates require fresh review while
completed tasks stay completed until explicitly reopened. See
[task lifecycle](docs/task-lifecycle.md).
Follow the [repeatable local demo](docs/demo-walkthrough.md) for the complete
Calendar → preparation → review → source-change flow.

Draft editing warns before leaving with unsaved changes and requests a browser
warning on reload/close. Save before updating a brief, checking Calendar or
removing a source. Concurrent saves are checked against the loaded draft; newer
briefs or drafts preserve unsaved text for explicit comparison and recovery.
Unsaved text is held in memory, not backed up across a closed tab or browser crash.
See the [development assessment and priorities](docs/development-plan.md).

Meeting dates use full month names, AM/PM times and explicit UTC offsets, keeping
the source's timezone rather than silently converting to the viewer's timezone.
Calendar source previews group the date and time range; original source text and
exact citation quotes remain available. Drafts containing ISO timestamps offer
Make dates readable as an explicit edit that can be reviewed and saved.

Workspaces and Connections check preparation availability every five seconds.
The worker reports a database heartbeat every ten seconds; a missing heartbeat
expires after 45 seconds. This distinguishes a running API from an available
preparation service without contacting Meta. Saved requests survive a worker
restart. Availability is not a provider-access or billing guarantee.

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

`check` runs TypeScript, ESLint, export/draft regression tests, Ruff lint/format checks,
and the API test suite.
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
The adapter targets `https://api.meta.ai/v1` with `muse-spark-1.3`; local catalog
access and synthetic preparations were verified. Credit expiry and overage
behavior remain unconfirmed. `GHOSTTAB_ALLOW_MODEL_REQUESTS=false` prevents admission
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
