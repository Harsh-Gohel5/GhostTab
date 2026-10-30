# Jira Meta evaluation — October 29, America/Phoenix

Two real Spark 1.3 requests used fictional Jira/email evidence through the existing
worker and strict schema/exact-quote validation. No private account data or live
connector reads. Latencies were 11.64 and 11.50 seconds; estimated usage cost was
$0.017387. The coding agent inspected the outputs against the written criteria:

| Case | Observed result |
| --- | --- |
| Conflicting approval | Exposed Blocked/pending versus email approval, missing approver and unknown precedence; draft remained unsent |
| Revised issue | Used In progress instead of earlier Blocked; kept approval pending/unassigned and Maya's ownership limited to the launch checklist |

Both met these narrow expectations. This is one sample per case, not a reliability
score or independent human evaluation. Quotes alone do not prove semantic support.
The revised-case draft asks whether to send it; GhostTab still offers no external
sending tool. [Sanitized trial report](evaluations/jira-trials-2026-10-29.json).

A separate authorized Wonder 1.0 review received only our own Jira implementation
source, with no credentials or user data. It failed `model_output_incomplete`
after 56.19 seconds, so no findings were accepted or acted on. Usage was unavailable;
the ledger retained the $0.189828 reservation conservatively. This is **not measured
spend**. No automatic retry was run. The result does not establish that Wonder
cannot review code; this bounded attempt produced no usable review.
[Failure report](evaluations/jira-review-2026-10-29.json).

The main ledger now totals $0.387755 including the retained review reservation,
within the unchanged $1 cap. Spark stays the app default. More requests or API keys
would not themselves demonstrate better model use; future trials should target
specific user-visible failures. These trials do not verify real Jira authorization.

Reproduce explicitly with owner authorization:
`.venv/Scripts/python.exe apps/api/tests/evaluate_jira.py --live`.
The optional `--review` sends bounded own-repository Jira source to Wonder.
Both reserve $0.20 in the main ledger first and use disposable evaluation storage;
no credentials are included as evidence. Raw local traces remain ignored.
