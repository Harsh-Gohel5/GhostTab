# Source-change review

November 1, 2026. A workspace with a visible saved brief now shows **What changed
since this brief** when active evidence differs from that brief's manifest.
Check Calendar, Check source or edit notes first; there is no automatic polling
or inference for this panel.

Expand a source to compare the version used in the brief with the current saved
version, including title/link changes. Text differences use a line comparison
bounded to 200 lines per side; longer sources show whole previous/current text.
Calendar text is formatted for readability. Exact original citation quotes remain
available under each claim and in the existing cited-source view.

Summary, fact and next-step claims are listed only when they explicitly cite the
updated source. This is dependency information, not a semantic claim that those
statements are wrong. Drafts/open questions have no individual citation mapping.
Added context is labeled separately; an uncited source gets no invented claim
dependencies. Comparison is against the saved brief, even after multiple edits.

**Update brief with current context** reuses normal Meta preparation. The button
respects unsaved draft edits, active jobs, service/configuration state and the
attempt limit. Existing backend budget checks still apply. A successful current
brief clears the panel; a failed/obsolete request preserves the previous baseline.

The workspace API computes `source_changes` from active owned evidence and the
already-visible snapshot/cited versions. No arbitrary history endpoint, migration,
provider read or new model request is added. Removing/disconnecting a manifest
source blocks its brief and comparison rather than exposing historical content.

Verification: 40 frontend tests (including actual component server rendering,
escaping, disabled actions and bounded diff reconstruction) and 136 API tests
passed with type/lint/format checks and the production build. Tests cover
cumulative edits, additions, unchanged/metadata-only updates, owner isolation,
Google refresh and disconnect blocking. Full interactive browser/layout testing
remains pending because local browser automation is unavailable.

Two opt-in real Spark trials used fictional Calendar/Docs representations in
disposable evaluation storage, with no live connector reads. Both passed worker
schema and exact-quote checks. Coding-agent inspection found the updated fact
correctly attributed Nina's accessibility review to the Doc, preserved Calendar
timing, left support unassigned and did not claim completion. Individual facts
were supported; the summaries used broader paraphrases than their selected quotes,
so this is not a claim of perfect per-sentence semantic citation coverage.
One sample per case is not a general accuracy score or an independently observed
browser workflow. Estimated usage: **$0.019944**, within the unchanged $1 app cap;
the existing $0.20 hold was reconciled by the evaluation helper. No additional key
or automatic retry was used.

Sanitized fictional report: [baseline/update trials](evaluations/source-changes-2026-11-01.json).
Reproduce only with owner authorization:
`.venv/Scripts/python.exe apps/api/tests/evaluate_source_changes.py --live`.
