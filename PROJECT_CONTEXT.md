# GhostTab project context

## Current recovery entry point — November 2, 2026

The latest verified application baseline includes PRs #17–18: a local-logo
connector gallery, two pages of 25/24 tools, and app-specific connection actions
that retain truthful availability. The owner confirmed the interface working.
PR #18 passed 51 frontend and 142 API tests, build and required web/API CI.

The repository is being organized on `chore/repository-organization`. Runtime
code, migrations, environment and data paths stay stable. Use the
[documentation index](docs/README.md), [repository guide](docs/repository-guide.md)
and [current status](docs/current-status.md). Older baseline counts and branch
names below are historical and do not override a fresh Git/process inspection.

The owner supplied event-detail screenshots confirming the submission deadline:
November 4, 2026, 9:00 PM EST / 7:00 PM MST in Phoenix. Public code, an accessible
three-minute video and contributor listing are required. Full remaining rules
and the submission form still need review; see the
[submission checklist](docs/submission/requirements.md).

Branch names now follow `feat/`, `fix/`, `docs/` and `chore/` conventions.
Prior local handoff files and branch references are preserved in ignored
`.ghosttab/repository-cleanup-20261102/`. No branch renaming rewrites commits.

Updated November 1, 2026 (America/Phoenix). Recovery baseline: `main` at
`9392fcd`, after readiness PR #16. This is a navigation and recovery guide, not
a replacement for the detailed documents linked below. Recheck volatile state
before acting; this file does not grant new provider access or spending authority.

## Start here

1. Read [AGENTS.md](AGENTS.md) for development and protected-main rules.
2. Inspect `git status --short --branch` and recent commits before changing files.
3. Use this guide, [README](README.md) and [release readiness](docs/quality/release-readiness.md)
   for the latest implemented baseline. Read [architecture](docs/architecture.md)
   before changing application boundaries.
4. Preserve `.env`, its encryption key, `.ghosttab/ghosttab.db` and accompanying
   SQLite WAL/SHM files. Do not reinstall, reseed, migrate or reconnect merely to
   recover context. First determine whether any such operation is necessary.
5. Check existing listeners and pending jobs before starting duplicate services
   or the worker. Starting the real worker can consume inference credit.

**Evidence labels:** “implemented” means present in code; “automated” means tested
with isolated/mocked inputs; “browser rehearsal” means observed in the disposable
UI; “owner-confirmed” records the owner's prior real-service use. None alone
establishes production readiness. Recommendations below are proposed next work.

## 1. Vision and objectives

**“Your next task, already in context.”** GhostTab prepares task workspaces for
people whose work spans messages, documents, meetings and task systems. Intended
audiences include operations, marketing, client services, support and engineering;
developer workflows are optional extensions of a shared task/evidence model.

The usable slice is explicit selection/import of authorized evidence, a Meta-backed
cited brief and editable unsent draft, human review, and visible context changes
after a manual source check. The longer-term ambition is less manual context
assembly; autonomous discovery and continuous synchronization are not shipped.

The project is a local prototype being developed for the Meta Global AI Developer
Hackathon. The internal release goal is one authentic workflow across at least
two services, real model reasoning, traceable evidence and a relevant source update.
This internal goal is distinct from independently verified organizer requirements.
Event rules/deadlines must be rechecked before submission. See [roadmap](docs/roadmap.md)
and [demo plan](docs/submission/demo-plan.md).

## 2. Architecture and stack

```text
React/TypeScript browser UI at 127.0.0.1:5173
  -> Vite /api proxy -> FastAPI/Uvicorn at 127.0.0.1:8000
                       -> owner-scoped SQLite data and durable job records
                       -> explicit authorized provider reads/OAuth
Separate Python worker -> claim leased job -> reserve estimated cost
                       -> bounded Meta request -> schema/quote validation
                       -> generation/lease checks -> saved brief and draft
```

| Layer | Current implementation |
| --- | --- |
| Frontend | React 19.3.1, TypeScript 6.0.3, Vite 8.3.5; npm workspace |
| State/contracts | TanStack Query, Zod; navigation uses React state, not React Router |
| Identity | Supabase JavaScript SDK; server-side PyJWT signature/claim validation; separate loopback-only local development mode |
| Backend | Python >=3.12, FastAPI, Uvicorn, Pydantic/settings, HTTPX |
| Persistence | SQLAlchemy 2, Alembic; SQLite locally, PostgreSQL supported and tested in CI |
| Model | Meta Chat Completions; `muse-spark-1.3` default; bounded Wonder evaluation support |
| Verification | TypeScript, ESLint, Node tests, Ruff lint/format, pytest, GitHub Actions |
| Reproducibility | `package-lock.json`, `requirements-dev.lock`, local `.venv` |

The observed local runtimes during recovery were Node 22.14.0 and Python 3.13.0.
Requirements and dependency versions come from the manifests/locks, not a claim
that these versions remain the latest available. No dependency upgrade is needed
just to resume development.

The backend is a modular monolith with separate API and worker processes. Migration
head is `0004`: initial task/evidence/preparation/Calendar schema, worker presence,
additional source grants, then review/completion state. Models include tasks,
evidence and immutable versions, jobs, snapshots, model runs, budget, Calendar
connections/OAuth state, source connections/references/OAuth state and heartbeats.
The actual implementation is owner-private; proposed organization/tenant sharing
in design prose is not implemented membership infrastructure.

There is no deployed GhostTab application, production static-asset serving,
Redis, Kafka, vector database or local Git bridge. Render/Supabase deployment
diagrams describe targets, not provisioned hosting.

## 3. Repository map

| Location | Purpose / useful entry points |
| --- | --- |
| `apps/web/src/App.tsx` | Session gate, main views and workspace composition |
| `apps/web/src/accountSession.ts` | Restoration deadline, auth-event ordering, account-bound tokens and partial sign-out feedback |
| `apps/web/src/api.ts` | Runtime-validated API contracts and request wrapper |
| `apps/web/src/DraftEditor.tsx`, `draftState.ts` | Draft editing, concurrency and unsaved-state recovery |
| `apps/web/src/SourceChanges.tsx`, `sourceDiff.ts` | Previous/current context comparison and cited claims |
| `apps/web/src/catalogData.ts`, `ConnectorCatalog.tsx` | Integration catalog and honest availability |
| `apps/web/src/styles.css` | Shared semantic palette, responsive and theme styles |
| `apps/web/tests` | Frontend regressions; opt-in SDK fixture integration is separate from default tests |
| `apps/api/src/ghosttab_api` | `main.py`, `routes.py`, `auth.py`, `config.py`, `models.py`, `database.py`, `workspaces.py`, provider modules, `worker.py`, `meta.py`, `readiness.py`, `source_changes.py` |
| `apps/api/migrations` | Alembic migrations `0001`–`0004` |
| `apps/api/tests` | API/provider/ownership/recovery tests, fake models, evaluation helpers and browser fixtures |
| `scripts/python.mjs` | Cross-platform launcher selecting the repository virtual environment |
| `.github/workflows/ci.yml` | Separate web/API jobs; PostgreSQL behavior and migrations in API job |
| `docs` | Detailed setup, architecture, feature contracts, evaluations and delivery plans |
| `.ghosttab` (ignored) | Real local database, backups, screenshots, local evaluations and release-check clone; not disposable as a whole |

## 4. Features and verification status

| Capability | Status and boundary |
| --- | --- |
| Today / Workspaces / Connections | Implemented; readiness, title/goal search, counts and lifecycle filters. Lists cover the latest 100 loaded workspaces. |
| Task evidence | Manual notes, selected imports, immutable revisions, provenance, removal and blocked derived content. |
| Preparation | Structured summary/facts/next steps with exact quotes, unknowns and editable unsent draft. Real fictional Meta trials are recorded; default API tests use fakes. |
| Durable execution | Deduplicated jobs, leases/recovery, bounded retries, cost reservations and generation-fenced publication; automated coverage. |
| Drafts and export | Concurrent-save protection, unsaved-navigation warnings, explicit conflict recovery, readable-date edit, copy and cited Markdown download. Unsaved text is memory-only. |
| Human progress | Review tied to current brief/draft, completion and reopening; separate from source freshness and AI preparation. |
| Source changes | Manual check/edit marks context stale; previous/current versions and citation dependencies shown; regeneration remains explicit. Browser comparison flow rehearsed with fictional data. |
| Account access | Email signup/confirmation/sign-in and Google identity sign-in owner-confirmed; recovery completion also owner-confirmed in the local release record. |
| Readiness auth hardening | Ten-second restoration UI deadline, late-response/unmount guards, account-bound credential lookup, partial-logout feedback. Unit, actual-SDK fixture and browser checks passed. |
| Themes/accessibility behavior | Persistent light/dark themes, profile initials, finite SVG ghost greeting, reduced-motion handling; not a comprehensive accessibility certification. |
| Integration catalog | 49 tools in 14 categories over two pages: six implemented flows, 43 unavailable integrations with explicit availability feedback, and local logos. No additional account access. |

| Source | Implemented boundary | Live verification |
| --- | --- | --- |
| Google Calendar | Read-only OAuth, selected primary-calendar events, manual refresh/disconnect | Previously live-verified; signed-in import/reconnect documented |
| Google Docs | Separate grant, selected document text, manual refresh/disconnect | Owner-confirmed two-source workflow; final independent Docs citation/update capture pending |
| Gmail | Read-only search/selection, single-message import, refresh/disconnect | Simulated-provider tests; live authorization pending |
| Slack | Selected public thread, refresh/disconnect | Simulated-provider/browser checks; live consent pending |
| Jira | OAuth, site and selected issue, refresh/disconnect | Simulated-provider/browser checks; live consent pending |
| Teams | Work/school selected chat, refresh/disconnect | Simulated-provider/browser checks; live consent pending |

Google identity sign-in does not authorize source reads. Each application identity
has separate source grants; old local-owner data is not silently migrated. Stored
grants and “Connected” labels do not prove a token currently works.

Details: [Google sources](docs/connectors/google.md), [Slack](docs/connectors/slack.md),
[Jira](docs/connectors/jira.md), [Teams](docs/connectors/teams.md),
[catalog](docs/connectors/catalog.md), [lifecycle](docs/product/task-lifecycle.md),
[draft/design behavior](docs/product/design.md), [source changes](docs/product/source-changes.md).

## 5. Technical decisions and safeguards

- Retain React/TypeScript and FastAPI. Add infrastructure only for a demonstrated
  need; local development must remain free. No paid hosting/purchases are authorized.
- Keep model output, source assertions, proposed actions and verified execution
  distinct. Source content and generated text are data, never tool instructions.
- Server ownership and grant checks protect reads, imports and publication.
  Tokens remain encrypted server-side. Do not expose credentials in `VITE_*`,
  chat, screenshots, commits or diagnostics. Supabase identity and provider grants
  are separate authorization boundaries.
- Source changes increment a task generation. Snapshot manifests preserve exact
  input versions. Removed access blocks derived snapshots, not just source links.
  Historical versions remain stored; physical purge is not implemented.
- One Meta request per attempt, at most three attempts per generation. The worker
  uses a 180-second job lease and estimated-cost reservations; uncertain billing
  retains reservations. Spark remains default because bounded Wonder comparisons
  did not demonstrate a clear benefit. Prompt version is `meeting-brief-v3`.
- Keep evidence bounded: eight active sources, 12,000 characters per source and
  4,000 completion tokens. Exact-quote checks do not prove semantic support.
- Worker presence is separate from API health: ten-second heartbeat, 45-second
  expiry; UI readiness polls every five seconds. A heartbeat does not prove Meta
  access, credit availability or output correctness.
- Recovery from an old Calendar failure checks grant identity before disconnecting
  a replacement connection. Explicit user disconnect remains unconditional.
- Use shared semantic light-neutral, indigo and teal tokens. Preserve clear status
  text and reduced-motion behavior.

See [architecture](docs/architecture.md), [model budget](docs/model-budget.md) and
[readiness](docs/quality/release-readiness.md) for implementation and tradeoffs.

## 6. Development and testing commands

Run from the repository root. Windows uses `npm.cmd` and explicit Python paths;
do not change execution policy or overwrite an existing environment to resume.

| Command | Purpose / caution |
| --- | --- |
| `npm.cmd ci` | Fresh-checkout locked frontend install; unnecessary when existing dependencies work |
| `python -m venv .venv` | Fresh checkout only; preserve an existing environment |
| `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock` | Locked Python dependencies on fresh setup |
| `.\.venv\Scripts\python.exe -m pip install --no-deps -e ./apps/api` | Editable backend installation |
| `npm.cmd run db:migrate` | Upgrade the configured database; inspect current revision and preserve data first |
| `npm.cmd run dev` | Frontend, loopback port 5173 |
| `npm.cmd run dev:api` | API with source reload, loopback port 8000 |
| `npm.cmd run dev:worker` | Real durable worker; can process queued work and consume credit |
| `npm.cmd run check` | TypeScript, ESLint, frontend tests, Ruff lint/format and API tests |
| `npm.cmd run check:web` / `npm.cmd run check:api` | Component checks for relevant changes |
| `npm.cmd run test:api` | API tests only |
| `npm.cmd run build` | TypeScript plus production web bundle in `apps/web/dist` |
| `npm.cmd run preview` | Local built-frontend preview on 4173; not production deployment |
| `.\.venv\Scripts\python.exe -m pip check` | Installed Python dependency consistency |

Windows reload-wrapper recovery, already documented and used successfully:

```powershell
.\.venv\Scripts\python.exe -m uvicorn ghosttab_api.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

This fallback has no reload: restart it after backend edits. Use only one API
arrangement at a time. Health is `http://127.0.0.1:8000/api/health`; development
docs are `/api/docs`; Vite proxies `/api` to the API.

Disposable browser tests require the built frontend:

```powershell
.\.venv\Scripts\python.exe apps/api/tests/browser_fixture.py
# Port 8010: synthetic task/source workflow, fake model, temporary database.
.\.venv\Scripts\python.exe apps/api/tests/auth_browser_fixture.py
# Port 8011: two fictional identities, auth failure controls, fake preparation.
node --experimental-strip-types --test --test-timeout=15000 apps/web/tests/sessionFixture.integration.mjs
# Run only while the port-8011 fixture is active; storage is test-owned memory.
```

Use the fictional credentials and controls in [readiness](docs/quality/release-readiness.md).
Neither fixture is the saved live demo. Keep failure cases disposable. Ordinary
tests use fakes; evaluation scripts with `--live` are separate, opt-in inference.

Use reasonable process deadlines (the readiness pass used 25–90 seconds), stop
stalled commands safely and investigate. Windows sandbox restrictions previously
blocked sockets, temporary SQLite and Vite SSR tests; retry necessary commands
through normal escalation, not by weakening application security. Do not rerun
successful tests without a relevant change or unresolved concern.

## 7. Git state, recent milestones and verification

Snapshot at document creation: `main`, HEAD `9392fcd`, matching the local
`origin/main` tracking ref. Existing untracked `CODEX_HANDOFF.md` and empty
`project_dump.txt` were preserved. This newly created document is initially
uncommitted; inspect current status rather than assuming this snapshot persists.

| Main commit | Milestone |
| --- | --- |
| `9392fcd`, PR #16, Nov 1 | Readiness hardening, Calendar replacement-grant fix, disposable two-account/session/Docs recovery evidence |
| `08cd0c0`, PR #15, Nov 1 | Recovery password update ends browser session and returns to sign-in |
| `639c341`, PR #14, Nov 1 | Source-version differences and cited claims to review |
| `fa43d63`, PR #13, Oct 31 | Live Calendar/Docs workflow checkpoint |
| `c8e360a`, PR #12, Oct 31 | Honest searchable connector catalog |
| `b1be945`, PR #11, Oct 30 | Google identity-provider availability check |
| `43dc01b`, PR #10, Oct 30 | Grounding correction and retained evaluation failures |

PR #16 used `codex/release-readiness` with five focused commits, then squash-merged
through GitHub after diff review, required web/API CI and no unresolved threads.
Local main was fast-forwarded from the protected remote. Never commit/push directly
to main, rewrite it or bypass protection. Future changes start from current main
on descriptive branches and follow [CONTRIBUTING](CONTRIBUTING.md).

November 1 pre-gallery checks: **47 frontend tests, 142 API tests, TypeScript/ESLint,
Ruff lint/format, production build and opt-in actual-SDK fixture integration passed.**
PR CI also passed PostgreSQL behavior and migrations. Browser evidence covers
restoration, A/B workspace isolation, cross-tab sign-out, unsaved-draft cancel/
discard and partial-logout feedback. These are recorded results, not tests rerun
while writing this document. See [PR #16](https://github.com/Harsh-Gohel5/GhostTab/pull/16)
and [its CI run](https://github.com/Harsh-Gohel5/GhostTab/actions/runs/41356721946).

Runtime rechecked for this document: ports 5173 and 8000 were listening; frontend
and proxied health returned HTTP 200; no listeners on fixture ports 8010/8011.
At readiness completion the Meta worker was stopped. Recheck process/queue state
before starting it; server/process handles from an earlier chat are not a supervisor.

## 8. Limitations, unresolved issues and uncertainty

- **Release gate:** real-provider expiry/reconnect and final two-live-account browser
  isolation remain pending. Synthetic success does not close these gates.
- **Evidence gate:** Calendar/Docs change/regeneration is owner-reported complete;
  independent final Docs citation and before/after capture remain pending.
- **Model quality:** quote/schema validity does not guarantee claim support. Small
  fictional trials retained semantic failures and overbroad summary paraphrases.
  No general accuracy score or measured productivity improvement is established.
- **Product scope:** no autonomous discovery, scheduled source sync, push/webhooks,
  automatic regeneration, sending/publishing, arbitrary attachments or local Git bridge.
- **Data behavior:** unsaved drafts have no crash recovery; disconnect blocks app
  access but does not purge historical data or revoke Google-side grants. Reconnect
  does not automatically resurrect removed evidence or blocked briefs.
- **Delivery:** no hosted GhostTab application; production routing, operational
  backups, judge access, video and final submission remain unfinished. Public email
  delivery requires appropriate SMTP setup; current identity success is not proof
  of general-public onboarding readiness.
- **Warnings:** large JS bundle, Alembic configuration deprecation and Starlette
  TestClient deprecation remain. Earlier dependency audit recorded 12 moderate
  development findings and zero production advisories; this is historical, not a
  fresh audit or a reason to upgrade the toolchain without compatibility checks.
- **Windows:** npm/Uvicorn reload wrapper can terminate after backend edits and
  cause proxy 502; the direct-command fallback restores service. Embedded-browser
  localhost access worked in the latest readiness pass; older claims that it was
  unavailable are historical, and the earlier failure's cause was not established.
- **Billing:** Meta is off by repository default. The last locally verified setup
  used enabled requests and a $1 cap. Credit expiry/overage remain unconfirmed;
  app estimates/reservations are not a provider billing guarantee. Do not increase
  limits or add keys merely to resume. The readiness pass made no live model calls.

## 9. Pending tasks and recommended next steps

Recommended order, preserving the working demo:

1. Prepare disposable real test accounts/resources for live account isolation and
   Calendar/Docs expiry/reconnect checks. Do not revoke the working demo's grants.
   Reuse completed synthetic regressions; fix only newly demonstrated defects.
2. Capture the authentic Calendar + Docs workflow, both source citations and the
   before/after change sequence. Review semantic support, not just quote presence.
3. Resolve findings, if any, on focused branches; run relevant checks/build and
   required CI, then merge through the protected PR workflow.
4. Decide and rehearse judge access using accurate local instructions or separately
   verified free delivery. Do not provision paid hosting. Finish screenshots/video
   and submission materials; recheck organizer requirements at that point.
5. Reconcile stale documentation as part of those milestones. Extra live connectors,
   automation and infrastructure wait until the core release gates pass.

These are recommendations, not claims that the remaining work was executed.
Do not repeat owner-confirmed password recovery or completed readiness checks
unless a relevant change requires it.

## 10. Documentation precedence and maintenance

| Need | Read |
| --- | --- |
| Current recovery summary | This file, then [readiness evidence](docs/quality/release-readiness.md) |
| Setup/configuration | [README](README.md), [setup](docs/guides/setup.md), [account access](docs/guides/account-access.md) |
| Current vs target architecture | [Architecture](docs/architecture.md), actual source and migrations |
| Historical live workflow evidence | [October 31 checkpoint](docs/current-status.md), [demo walkthrough](docs/guides/demo-walkthrough.md) |
| Model results and limits | [Grounding evaluation](docs/evaluations/grounding.md), [source changes](docs/product/source-changes.md), [model comparison](docs/evaluations/model-comparison.md) |
| Scope/delivery priorities | [Roadmap](docs/roadmap.md), [development plan](docs/archive/development-plan.md), [demo plan](docs/submission/demo-plan.md) |

Many detailed docs accumulate dated checkpoints. `docs/current-status.md` still
has an October 31 heading; `CODEX_HANDOFF.md` describes October 27 and an obsolete
branch. Their pending-PR/feature statements must not override newer commits and
November 1 readiness evidence. Preserve them as history rather than treating them
as instructions to redo setup or reopen superseded work.

Maintain this file after meaningful milestones: update the baseline commit/date,
verification boundary, remaining gates and links. Keep private identities, source
contents, tokens, grant values and session artifacts out of it. Prefer links over
copying detailed setup procedures, evaluation ledgers or speculative architecture.
