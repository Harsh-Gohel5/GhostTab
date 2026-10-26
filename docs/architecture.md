# Architecture and foundation decisions

Status: initial foundation, October 26, 2026.

## Product boundary

GhostTab prepares a useful starting state for a developer task. It should explain
why each source belongs, identify the revision that supports it, and distinguish
observed facts, model hypotheses, unknowns, and execution results.

## Implemented today

```text
Browser on 127.0.0.1:5173
  -> Vite development proxy /api
    -> FastAPI on 127.0.0.1:8000
      -> GET /api/health
```

The frontend and API are separate applications in one repository. TypeScript
uses strict checking; the backend uses Pydantic settings and response models.
There is no database, queue, connector, model adapter, or local bridge yet.

## Decisions

| Decision | Reason |
| --- | --- |
| React + TypeScript + Vite | A small, fast interface foundation with explicit types |
| Python + FastAPI | A straightforward API and a suitable home for model and retrieval orchestration |
| npm workspaces for JavaScript | One frontend lockfile and shared root commands |
| Local Python virtual environment | Isolated backend dependencies without global installation |
| API proxy during development | A single browser origin without permissive CORS |
| Defer database and queue setup | Introduce infrastructure alongside a concrete persistent workflow |
| Defer Kafka and a general DAG engine | Current scope does not establish a need for them |

## Planned component boundaries

| Component | Responsibility |
| --- | --- |
| Web interface | Tasks, source evidence, freshness, preparation progress |
| API | Authentication, grants, task and snapshot access |
| GitHub connector | Authorized issue, comment, code, PR and commit retrieval |
| Preparation worker | Bounded retrieval, model synthesis, validation and assembly |
| Model adapter | Meta-backed grounded briefs, gaps and evidence selection |
| Persistent store | Tasks, source versions, immutable snapshots and job state |
| Local bridge | Authenticated local checkout creation and editor opening |
| Optional execution environment | Reproduction runs with explicit results and resource limits |

A hosted API cannot directly create a checkout on a developer's computer. That
requires a local bridge. A Git worktree isolates working files; it is not an
execution sandbox.

## Invariants for implementation

- Verify webhook signatures before accepting event work.
- Enforce source authorization at retrieval and display boundaries.
- Treat repository content, messages and model output as untrusted data.
- Bind snapshots to source IDs, source revisions, commit SHA and retrieval time.
- Reject model citations and file paths that are not supported by retrieved evidence.
- Deduplicate delivery IDs and task/source revisions; retries must not duplicate workspaces.
- Mark stale context visibly and preserve it while preparing its replacement.
- Show missing, proposed, executed, failed and confirmed reproduction states distinctly.
- Publishing code or sending external replies remains a deliberate user action.
- Use synthetic or explicitly authorized code and data for demonstrations.

The first model and connector integration must verify actual access and model
identifiers. The original concept's references to Meta connectors do not establish
ready-made access to every external service.
