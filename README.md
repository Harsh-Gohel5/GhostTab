# GhostTab

**Your next task, already in context.**

GhostTab turns selected meeting and document evidence into a task workspace with
a cited brief, open questions, and an editable draft. When a manually checked
source changes, the workspace shows what changed and flags preparation that needs
review. Nothing is sent on your behalf.

Built for people whose work spans meetings, messages, documents, and task tools.
The current demonstrable workflow uses Google Calendar and Google Docs with
Meta's Muse Spark through the Meta Model API.

## How it works

1. Choose a meeting or create a workspace.
2. Import the sources you want GhostTab to use, or add notes.
3. Request a brief with source quotations, uncertainties, and a draft next action.
4. Review and edit the result. Check sources later to compare changes and update it.

## What is available

| Capability | Current status |
| --- | --- |
| Workspaces, evidence, briefs, drafts, review and completion | Implemented and tested |
| Google Calendar + Google Docs workflow | Exercised by the owner in the local app |
| Gmail, Slack, Jira and Teams connection flows | Implemented and tested with simulated providers; live verification varies |
| Source comparison and stale-context warnings | Explicit manual checks; no continuous synchronization |
| 49-tool connection gallery | Two pages with logos and connection options; 43 integrations are unavailable |
| Account access and session recovery | Supabase identity with automated isolation/recovery checks |
| Hosting | Local application; no public deployment claimed |

See [current status](docs/current-status.md) for verification boundaries and
[release readiness](docs/quality/release-readiness.md) for deferred checks.

## Run locally

Requires **Node.js 22.12+**, **Python 3.12+**, npm and Git. These instructions are
for a fresh checkout. Preserve an existing `.env`, virtual environment and database.

Windows PowerShell:

```powershell
npm.cmd ci
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e ./apps/api
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm.cmd run db:migrate
```

Start the API and frontend in separate terminals:

```powershell
npm.cmd run dev:api
```

```powershell
npm.cmd run dev
```

Open [GhostTab](http://127.0.0.1:5173/) or check
[API health](http://127.0.0.1:8000/api/health).
For macOS/Linux, connector configuration, identity and the preparation worker, see
the [setup guide](docs/guides/setup.md). Starting a configured worker can consume
model credits; opening the app does not trigger model requests.

## Development commands

Run from the repository root. PowerShell users can use `npm.cmd` in place of `npm`.

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Vite frontend |
| `npm run dev:api` | Start the FastAPI backend |
| `npm run dev:worker` | Start the preparation worker when authorized/configured |
| `npm run check` | Documentation links, frontend and backend checks/tests |
| `npm run check:docs` | Check local Markdown links |
| `npm run build` | Type-check and build the frontend |
| `npm run db:migrate` | Apply database migrations when needed |

## Repository map

```text
apps/
  web/                     React / TypeScript interface and frontend tests
  api/                     FastAPI service, durable worker, migrations and tests
docs/
  guides/                  Setup, account access and walkthrough
  product/                 User workflows and design decisions
  connectors/              Provider setup and integration boundaries
  evaluations/             Model trials and sanitized result artifacts
  quality/                 Release-readiness checks
  submission/              Hackathon requirements and demonstration plan
  archive/                 Historical checkpoints, preserved for context
scripts/                   Development utilities
.github/                   CI and pull-request template
```

[Documentation index](docs/README.md) · [Architecture](docs/architecture.md) ·
[Project context](PROJECT_CONTEXT.md) · [Contributing](CONTRIBUTING.md) ·
[Submission checklist](docs/submission/requirements.md)

## Safety and limitations

Provider grants remain separate from identity sign-in. Credentials stay on the
backend; never put them in `VITE_*` variables. Local data lives in ignored
`.ghosttab/`, and configuration in ignored `.env`. Do not commit either.

Briefs are suggestions to review. Valid quotations alone do not prove a claim is
correct. GhostTab does not autonomously discover all relevant sources, continuously
sync accounts, or send drafts. Real provider expiry/reconnection and additional
account-consent checks remain deferred for broader release.

Third-party brand assets retain their own rights and notices; see
[asset attribution](apps/web/public/connectors/ATTRIBUTION.md).
