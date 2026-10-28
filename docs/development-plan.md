# Development assessment and next milestones

Reviewed October 27, 2026 against source, Git history, GitHub and local runtime.
Preserve the shared task/evidence model, React/FastAPI architecture and approved
palette. A developer audience can use this workflow without a developer-only rewrite.

## Verified baseline

| Area | Status and remaining boundary |
| --- | --- |
| Calendar task workflow | Implemented: selected event, manual notes, brief, citations, editable unsent draft, manual source check and stale/update flow. Live Calendar read passed during this assessment. |
| Meta preparation | Implemented; prior live synthetic calls are documented. This assessment uses mocked inference. Citation matching does not establish claim support. |
| Reliability | Persisted jobs, bounded retries, leases, budget reservations, source revisions and owner checks are implemented and tested. |
| UI | Today readiness, Workspaces, Connections and review navigation are implemented. Copy/export is carried forward from the closed, unmerged PR #6. |
| Local runtime | Frontend/API/proxy health passed; database is at migration 0001 with four saved successful preparations. The API was restored during verification. No schema change is needed for draft safety. |
| Hosted operation | Partial: PostgreSQL and Supabase paths exist; live hosted identity, production assets, backups and judge access are unverified/unimplemented. |
| Other integrations | Missing: mail/chat/document retrieval, scheduled sync, broad discovery and automatic preparation. Only Calendar is authorized. |
| Evaluation/submission | Missing: representative claim-support trials, measured benefit, final video and submission packet. |

The baseline passed TypeScript, ESLint, three export tests, Ruff and 25 API tests.
Windows sandbox restrictions stalled the first API test invocation; the normal
command passed outside that sandbox. No failing baseline application test was found.

## Priorities and completion gates

| Order | Milestone | Why / completion gate | Dependencies |
| --- | --- | --- | --- |
| 1 | Safe draft editing — implemented locally | Navigation/replacement protection, concurrent-save checks and save-response handling. Automated checks and synthetic browser workflow pass; PR approval is pending. | Existing snapshots and draft API; no new service or schema. |
| 2 | Evidence-backed demo evaluation | Rehearse Calendar → notes → preparation → review/export → source change → update. Record claim support, latency, failures and estimated cost across 5–10 synthetic trials. Correct inaccurate setup/architecture prose. | Current Calendar grant and explicitly authorized bounded model use. Decide PR #6 disposition before integrating changes into main. |
| 3 | Operational recovery | Add meaningful worker/configuration readiness and safe actionable errors; exercise restart, retry, budget and revoked-access behavior. | Findings from rehearsal; keep source freshness separate from worker status. |
| 4 | Reproducible judge access | Verify clean-clone setup and a clearly labeled synthetic sample. Decide local versus verified free hosting; hosted auth/HTTPS/asset serving need implementation if chosen. | User-approved delivery approach; no paid deployment. |
| 5 | Freeze and submit | Accurate README/screenshots, rehearsed three-minute video, final track/theme, submission checklist and organizer recheck. | Evaluation and judge-access gates. |

Do not add connectors, infrastructure or automatic sending to fill a checklist.
A second live source requires account authorization; it remains an internal product
goal, not a requirement established by the organizer page. PR creation and merging
require the owner's approval. This assessment does not authorize either.

## Hackathon alignment

The [organizer event page](https://cerebralvalley.ai/e/meta-ai-developer-hackathon),
checked October 27, lists indie/startup tracks, Build for Your World / Push the
Frontier themes, and submissions due November 4 at 9 PM ET (7 PM Phoenix).
GhostTab's grounded work preparation fits Build for Your World; final entry choice
remains the owner's. Meta Model API is already part of the implementation.
The page does not independently establish the detailed scoring weights, team limit,
public-repository requirement or video specifications transcribed in the handoff;
confirm those against the participant rules/submission form before submitting.

## Isolated browser verification

Run `npm run build`, then
`.venv/Scripts/python.exe apps/api/tests/browser_fixture.py` and open
`http://127.0.0.1:8010`. This serves the real built UI and API against a temporary
synthetic SQLite database. Preparation uses the test fake, not a network model.
Calendar and hosted authentication are intentionally absent. Stopping the server
normally disposes the temporary database; the normal app/database are untouched.

Exercise prepare, edit, canceled navigation/reload, save/reopen, two-tab conflicting
saves, source update/new preparation, compare/keep/latest draft choices and export.
The fixture validates application behavior, not live model quality or provider access.

Verification for this milestone: `npm run check` passed TypeScript, ESLint, nine
export/draft tests, Ruff and 28 API tests; `npm run build` passed with the existing
bundle-size warning. Browser checks passed prepare, edit/save/reopen, canceled
navigation, Escape and deliberate discard, two-tab conflict detection/comparison,
new-brief conflict recovery, clipboard and an actual Markdown download. The file
contained the edited draft and the updated source quote. A 320px viewport had no
horizontal overflow. Browser reload/close warnings use `beforeunload`; browser
support and crash recovery are not guaranteed. PostgreSQL CI was not rerun because
no PR creation was authorized and no disposable local PostgreSQL was configured.

On this Windows session the npm/Uvicorn reload wrapper stopped after source edits
and printed `Terminate batch job (Y/N)?`. The API was restored using the documented
direct command below; it has no automatic reload, so restart it after backend edits:

```powershell
.\.venv\Scripts\python.exe -m uvicorn ghosttab_api.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

## Milestone file changes

- Web: `App.tsx`, `DraftEditor.tsx`, `ConfirmDialog.tsx`, `draftState.ts`,
  `PreparationStatus.tsx`, `api.ts`, `styles.css`, `tests/draftState.test.mjs`,
  and `apps/web/package.json`.
- API: `contracts.py`, `routes.py`, `tests/test_workspaces.py`,
  and `tests/browser_fixture.py`.
- Documentation: `README.md`, `docs/architecture.md`, `docs/design.md`,
  `docs/demo-walkthrough.md`, and this assessment.

The original untracked `CODEX_HANDOFF.md` is preserved unchanged. Work is local on
`codex/draft-safety`, carrying the existing copy/export commit from
`feat/workspace-takeaways`. No commit, push, PR creation or merge was performed for
this milestone. No database migration, credentials, budget or provider scopes changed.
