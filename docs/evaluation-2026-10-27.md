# Live Calendar rehearsal — October 27, 2026

This is one fictional scenario through the real Calendar adapter and Meta API,
not a user study or proof of general output reliability. All scenario content is
synthetic. No credentials, provider event IDs or source links are recorded here.

## Initial preparation

Selected a future event named Demo: client launch, October 28, 9–10 AM,
America/Phoenix. The description assigns Maya the launch checklist, gives Lee a
Thursday-noon delivery-plan approval deadline and leaves support contact unassigned.
Added a visibly manual note asking to include the delivery checklist in the agenda.
Prepared once through the normal UI button and existing worker, under the unchanged
$1 cumulative application ceiling.

| Measure | Observed result |
| --- | --- |
| Model / prompt | muse-spark-1.3 / meeting-brief-v1 |
| Attempts | One successful submission |
| Job creation to snapshot publication | 7.90 seconds; includes queue wait, model request, validation and publication |
| Reservation to snapshot publication | 7.16 seconds; not an isolated model latency measurement |
| Input / output tokens | 892 / 2,154 (885 reasoning tokens included in output) |
| Estimated preparation cost | $0.010270; application estimate, not a reconciled provider invoice |
| Structure / citation integrity | Passed application validation; deadline quote inspected in the UI |
| Brief support | Correctly reflects ownership, deadline, missing support contact and manual agenda request. Next steps are proposals. |

## Quality issues found

The generated draft called the October 28 meeting “today” even though the current
date was October 27. Its suggested agenda also attached Maya to the delivery
checklist, while the source only assigns the launch checklist to Maya. These are
substantive draft-review findings; matching citations in the brief did not prevent
them. The saved draft was manually corrected to the explicit meeting date, removed
the ambiguous checklist attribution and labeled the agenda suggested.

Prompt v2 now asks for the explicit source meeting date and timezone, prevents
transferring ownership between differently named deliverables, and labels proposed
agendas suggested. This improves instructions; it does not guarantee future output
correctness. Existing successful generations remain deduplicated. Verification of
v2 should use the next source revision, not a hidden rerun of unchanged evidence.

## Pending update test

The reviewed draft was saved, copied and downloaded as Markdown through the live
UI. Clipboard verification confirmed the explicit October 28 meeting date.
Regression checks after the prompt edit passed TypeScript, ESLint, nine frontend
tests, Ruff and 28 API tests. This is not evidence that every future draft will
avoid the observed quality issues.

The owner is changing only the fictional event's approval deadline to Thursday at
3 PM, America/Phoenix. Next: manually Check Calendar, inspect the stale brief and
original noon quote, then Update brief once and review the 3 PM result and draft.
The full rehearsal is incomplete until those steps pass.

On the next manual API refresh, the event schedule changed to October 29,
1:30–3 PM Phoenix, but its description still stated Thursday at noon. GhostTab
correctly marked the prior brief stale and preserved its snapshot and original
noon quote. The browser automation connection was unavailable, so these checks
used the same API endpoint as Check Calendar. No second preparation was submitted:
the intended description/deadline change still needs to be saved in Calendar.
