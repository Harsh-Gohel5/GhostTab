# GhostTab whiteboard defense

This is an explanation of the **proposed architecture**, grounded in the current
React/FastAPI foundation. Do not describe planned components as deployed or claim
production scale before it has been measured. See [architecture](architecture.md).

## Opening explanation

“GhostTab prepares the context for a person's next task across their work tools.
It connects authorized sources, groups relevant evidence, uses a Meta model to
prepare a brief and draft next steps, and refreshes that workspace when relevant
information changes. The user can inspect why each item belongs and what remains
uncertain. The first workflow is an approval request spanning mail, chat and a
document; engineering workflows use the same core model.”

Draw four boxes: **interface → API → PostgreSQL ← worker**. Connect the worker to
source providers and Meta Model API. Add application authentication beside the
API. Explain the data flow before adding infrastructure details.

## What is implemented today?

The repository has Today/Workspaces/Connections in React/TypeScript, a FastAPI API,
SQLAlchemy/Alembic persistence, source revisions, jobs/worker/leases, bounded Meta
submission with citation validation and a usage ledger, plus Google Calendar OAuth
and manual refresh adapters. Local development uses SQLite and a loopback identity;
PostgreSQL and Supabase JWT verification are supported paths. Adapter tests mock
provider responses. Live OAuth, actual inference and hosted deployment are pending.
Meta requests are off by default. The health check proves process liveness only.

The owner currently has Google Calendar available. The first concrete slice is
meeting context, supplemented by clearly labeled manual notes. The mail/chat/doc
story above is the wider product direction, not a claim of shipped connectors.

## Why this architecture?

| Question | Defensible answer |
| --- | --- |
| Why React and TypeScript? | The interface needs explicit task/source states and interactive evidence review. Strict types help keep API and UI contracts understandable; runtime validation is still required. |
| Why FastAPI? | It gives a small typed API and a practical Python home for retrieval, model adapters and validation. It does not make background work durable by itself. |
| Why a modular monolith? | One small team can change the task/evidence workflow together. Module boundaries preserve separation without distributed deployment and transaction overhead. |
| Why a separate worker? | Provider latency and inference should not hold an HTTP request open. Durable jobs expose progress, retries and recovery. |
| Why PostgreSQL? | Users, grants, tasks, source versions and snapshots have relationships, uniqueness constraints and transactional publication requirements. JSONB accommodates provider-specific metadata. |
| Why no Redis or Kafka initially? | A Postgres job table satisfies the first durable workflow with fewer moving parts. Queue lag, throughput and independent consumers would provide reasons to revisit that decision. |
| Why no vector database initially? | The first flow has explicit links and selected sources. Full-text search is a bounded next step; embeddings should earn their complexity through retrieval evaluation. |
| Why no WebSockets? | The interface mainly needs occasional one-way progress updates. Polling active jobs is adequate initially. |

## Where does the model help?

The Meta model interprets a bounded evidence packet: it summarizes the task,
identifies missing or conflicting information, explains relevance and prepares
reviewable next steps. `muse-spark-1.3` Standard is the proposed default; Wonder
is an optional evaluated escalation.

Ordinary application code authenticates, retrieves authorized material,
deduplicates deliveries, validates references, manages revisions and executes
approved effects. A model never gets authority merely because a source message
says “send this” or “ignore prior instructions.”

“Every citation exists” is a necessary validation condition, not proof of factual
correctness. Evaluate claim support with representative tasks and human review.
Record prompt/model versions, input manifests and usage so failures are traceable.

## How do you avoid cross-user leaks?

Verify the application JWT and derive tenant membership on the server. Keep
provider tokens encrypted server-side. In the MVP, imported evidence is private
to the authorizing owner; organizational membership alone grants no mailbox or
private-message access. Filter before retrieval/model calls and check again
before display. Supabase RLS can add protection, but privileged backend database
roles may bypass it, so application authorization remains explicit.

Source revocation invalidates access to derived snapshots immediately. Rebuild
without revoked evidence or delete derived content as required. Simply hiding a
source link would still leak its content through the generated summary.

## How do you keep the workspace current?

Record exact source versions as snapshot dependencies. A source change marks
affected snapshots stale and queues a replacement. Also match newly arrived
items against active task rules; otherwise an important new message could be
missed because it was never a dependency.

Each task has a generation, and each prepared result has an input fingerprint
including source versions, query rules, grant epochs and model/prompt settings.
Check them before publication. A slow older job must not overwrite a newer
generation. Keep freshness independent of task status: a completed or waiting
task can still receive new context.

## What happens when things fail?

- Duplicate deliveries: durable provider-event keys prevent duplicate ingestion.
- Crashed workers: leases expire and a reaper schedules bounded retries.
- Provider/model timeouts: retry transient errors with backoff; preserve visible
  incomplete/error states rather than presenting success.
- Changed inputs during inference: supersede the obsolete result before publish.
- Invalid model references: reject the proposed output; never silently invent
  missing evidence.
- Exhausted inference budget: stop further calls and preserve manual access and
  authorized existing context.

Claim jobs in a short transaction, release locks before external work, heartbeat
the lease, and verify lease ownership/generation when completing work. The claim
is **at-least-once processing with idempotent effects**, not exactly-once execution.
An external model request can complete even if its network response is lost;
bounded retries and request accounting limit the resulting uncertainty and cost.

## How would you scale it?

Measure first: preparation latency, queue lag, provider throttling, database query
time, error rate, citation validity, cost per prepared task and time to a useful
workspace. Add worker capacity within provider rate limits, index hot queries,
and coalesce repeated changes. Separate services or add streaming infrastructure
only when a measured bottleneck or ownership boundary requires them.

For a convincing demonstration, show a real authorized request becoming a
workspace, inspect its evidence, introduce a relevant change, and observe a
correct refresh. Compare the complete workflow with manual context assembly,
including the time spent checking GhostTab's output. Report measured results
and limitations; winning and productivity improvements are not guaranteed.
