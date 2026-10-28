# Preparation availability checkpoint

Implemented locally on `codex/preparation-readiness`, from protected main at
`2b8cfd5`. This is a review checkpoint; no PR has been created for this milestone.

## Behavior

Workspaces and Connections show ready, offline, disabled, unconfigured or
budget_exhausted. The authenticated API exposes only aggregate status. Checking it
does not contact Google or Meta. A recent worker heartbeat signals process
presence, not provider access, output quality or a billing guarantee.

Each worker writes every 10 seconds on a separate thread, including during a slow
model call. A heartbeat expires after 45 seconds; normal shutdown removes that
worker's record. Multiple workers are independent. Job leases and retry/budget
limits remain responsible for execution and recovery.

The UI pauses new and retry actions while availability is unknown or unavailable.
Saved brief review and draft editing remain usable. Queued requests remain durable
and can resume after restart without duplicate submissions. Direct API admission
continues to allow durable work even when no worker is present.

## Verification

- `npm run check`: TypeScript, ESLint, 19 frontend tests, Ruff, 34 API tests pass.
- `npm run build` and `git diff --check` pass. The existing bundle warning remains.
- Tests cover configuration/budget states, expiry, multiple workers, presence during
  blocked inference, owner identity, queued-work restart, deduplication and an
  additive SQLite upgrade preserving an existing task.
- Browser: offline guidance appeared in Connections and a saved workspace; Review
  brief and draft editing stayed enabled. Restarting the worker changed the status
  back to available without a new model request.
- Migration 0002 applied locally after a SQLite backup. Before/after: five tasks,
  six snapshots and six succeeded jobs; estimated ledger stayed at $0.053162.
- PostgreSQL behavior and migrations still require PR CI. No deployed environment
  or fresh live model test is claimed. Alembic reports an existing configuration
  deprecation warning in the new migration test; it does not fail the upgrade.

## Proposed PR

**Title:** Show preparation availability and recovery guidance

The API could appear healthy while no worker was available, leaving requested
preparations waiting without an explanation. Add persisted worker presence and an
authenticated readiness endpoint, display distinct setup/budget/offline states,
and explain durable recovery while preserving saved content. Includes additive
migration 0002, heartbeat/restart/upgrade coverage and updated setup documentation.

Changed areas: API models/routes/worker plus new `readiness.py` and migration;
frontend API, App, PreparationStatus and new PreparationAccess/readiness hook/copy;
regression tests, isolated browser fixture, README, architecture and setup docs.

The original untracked handoff and all local credentials/data remain excluded.
After owner approval, publish the focused PR, require passing web/api CI and review
conversations, then squash-merge promptly under the protected-main workflow.
