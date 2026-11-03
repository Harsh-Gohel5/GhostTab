# Human review and task completion

October 28, 2026. Workspaces now persist human progress separately from AI
preparation readiness. Migration `0004` adds nullable review/completion fields;
existing workspaces start active and unreviewed. Source revisions and Calendar
grants are unchanged. Apply `npm run db:migrate` before starting this version.

## Decisions and freshness

- **Mark brief reviewed** records the owner's review of the current visible brief
  and exact saved draft. It requires a current source generation. Generated content
  is never automatically marked reviewed. Review does not establish factual accuracy.
- New source context, removed access, or a new brief prevents the previous review
  from counting as current. Editing and saving a different draft clears review;
  an identical draft save preserves it. Unsaved edits block progress controls.
- **Mark complete** records the user's decision that this task is finished. It
  needs neither AI nor source context and does not send a draft or execute work.
  Already requested preparation jobs are not canceled by completion.
- **Reopen workspace** returns a task to active without deleting its sources,
  snapshots or draft. A still-current review is preserved.
- Source changes after completion keep the task completed and show **context
  changed**. The owner decides whether to reopen; the application does not silently
  reverse a completion decision. This warning reflects saved source generations,
  not continuous provider synchronization. Draft edits clear review but do not
  count as a source-context change or automatically reopen a completed task.

Workspaces defaults to **Active**, with **All**, **Reviewed**, **Completed** and
readiness filters available. Today excludes reviewed/completed work from Needs
attention and Ready to review, and provides dedicated filters to find them.

## API and verification

`POST /api/tasks/{id}/lifecycle` accepts `review`, `complete`, or `reopen`. Owner
checks and the existing task lock serialize decisions with source/draft edits.
The request includes the loaded generation and completion timestamp; review also
checks the exact snapshot ID and saved draft. Stale requests fail with 409 and
the UI reloads current state. This is current progress state, not a full audit log
of all prior review/completion/reopen decisions.

Checks pass 23 frontend and 68 API tests, lint/type checks, and the production build
(existing large-chunk warning). Tests cover persistence, reopen, source-change and
draft-edit invalidation, whitespace preservation, conflicting status/draft requests,
source removal, owner isolation and completion without inference. Migration checks
preserve an existing task. PostgreSQL CI remains pending an approved PR.

The regular app is http://127.0.0.1:5173/. Browser rehearsals use the prominently
labeled synthetic fixture at port 8010 with a fake model and disposable storage;
they do not change real workspace progress or consume Meta credit.

Browser verification passed prepare with the fake model, mark reviewed, block
progress changes while draft edits are unsaved, clear review on a changed draft
save, re-review/complete, find the task under Completed, preserve completion with
a source-change warning, and explicitly reopen into stale/unreviewed state.
