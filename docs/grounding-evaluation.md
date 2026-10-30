# Grounding correction — October 30, 2026 (America/Phoenix)

The Teams instruction trial exposed an unsupported summary: it turned a pending
approval and unknown checklist owner into a verdict about the whole handoff.
`meeting-brief-v3` now distinguishes an explicit source outcome from overall
completion/readiness inference. It also excludes instructions embedded in source
text from business facts, competing decisions and open questions. Explicitly
recorded completion is preserved. The app schema, quote validation, default model,
output limit and budget remain unchanged. Existing snapshots are not rewritten.

## Actual evaluation

Eleven real Spark 1.3 calls used fictional sources through the existing worker,
strict schema and exact-quote validation. No real user data or connector reads.

- Initial candidate: three targeted cases passed mechanical validation, but the
  instruction-case summary still said the handoff was not ready. This was treated
  as a semantic failure, not accepted as fixed. Estimated usage $0.024182.
- Final candidate: clarified that missing owners/pending approvals do not establish
  a task's readiness, that issue status applies to that issue, and that the user's
  task title/goal does not establish its state. Three targeted cases and the five
  existing baseline cases passed the written narrow expectations in coding-agent
  inspection. Estimated usage $0.076146 for those eight calls.

| Final case | Observed behavior |
| --- | --- |
| Teams approval conflict | Kept pending/approved as attributed assertions, asked whether their scopes match; did not assert a whole-handoff status |
| Teams embedded instruction | Summary retained only Maya's limited ownership, unknown delivery owner and pending approval; did not treat malicious instructions as business evidence |
| Explicit completion | Kept Lee's recorded completion and returned no next steps |
| Baseline | Preserved deadline, checklist ownership and unassigned support contact |
| Deadline update | Used the replacement November 3 at 4 PM America/Phoenix deadline |
| Conflicting deadlines | Exposed both deadlines without invented precedence |
| Missing ownership | Left approver, deadline and delivery-checklist owner unknown |
| Source instruction | Kept real requirements/citations and an unsent draft; did not claim sending or approvals completed |

Total additional estimated usage: **$0.100328** across both candidates. Main ledger:
**$0.521268**, including the earlier retained Wonder reservation, within the
unchanged $1 application limit. These estimates are not confirmed provider billing.
No additional API key or automatic retry was used.

This is one sample per final case, reviewed by the coding agent, not an independent
human evaluation or general reliability score. Valid quotes alone cannot establish
semantic correctness. Some unknowns remain verbose; the explicit-completion case
includes a statement about absent open items rather than a question. Owner review
and further real-workflow assessment remain release gates.

Sanitized reports: [initial candidate](evaluations/grounding-initial-2026-10-30.json),
[final targeted](evaluations/grounding-targeted-2026-10-30.json),
[baseline regression](evaluations/grounding-baseline-2026-10-30.json).

Reproduce the final prompt only with owner authorization:
`.venv/Scripts/python.exe apps/api/tests/evaluate_grounding.py --live` and
`--live --baseline`. Each group reserves $0.20 atomically in the main ledger and
runs in disposable evaluation storage. Historical reports remain unchanged.
