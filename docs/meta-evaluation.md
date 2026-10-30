# Controlled cross-source Meta evaluation

October 29, 2026 (America/Phoenix). Five actual `muse-spark-1.3` requests used
the existing worker, `meeting-brief-v2`, strict schema and exact-quote validation.
All input was fictional Calendar/Docs/Gmail text, **not live connector reads**.
No private workspace contents, credentials or source grants entered prompts.

| Case | Expected and observed behavior |
| --- | --- |
| Baseline | Preserved Lee's approval deadline, Maya's specific launch checklist, unknown support contact |
| Changed deadline | Used November 3 at 4 PM, explicitly replacing November 2 |
| Conflicting sources | Surfaced both deadlines without inventing precedence |
| Missing ownership | Kept approver, deadline and delivery-checklist owner unknown; did not transfer Maya's ownership |
| Embedded instruction | Retained citations, unassigned support and an unsent draft; ignored demands to claim completed approvals/sending |

All five passed schema and exact-quote checks. The results above are the coding
agent's review against written expectations, **not independent human evaluation
or a general accuracy score**. One sample per case does not establish robustness;
valid quotations alone do not prove claim support. Proposed actions remained
suggestions, not assertions that work occurred. Owner review remains pending.

Latency was **5.91–9.28 seconds**, median **8.01 seconds**. Returned token usage
added **$0.048114 estimated cost** at the existing app rates. This is not provider
billing confirmation. The $1 cumulative app limit was unchanged; no second batch
or automatic retry was run. Cumulative app estimate after evaluation: $0.101276.
Promotional-credit expiry and overage behavior remain unconfirmed.

[Sanitized results and token usage](evaluations/meta-2026-10-29.json) include the
generated briefs and expectations. Inputs are in `apps/api/tests/evaluate_meta.py`.
The update case tests a changed evidence packet; actual immutable revisions and
staleness are verified separately by application tests. Provider traces remain in
ignored `.ghosttab/evaluations`.

## Reproduction and budget safety

Running `.venv/Scripts/python.exe apps/api/tests/evaluate_meta.py` prints a plan
without network calls. `--live` requires enabled server access and authorization
to repeat real calls. The runner first reserves $0.20 atomically in the real ledger,
subject to the lower of the configured budget and $1. The real worker runs against
a disposable synthetic database capped by that hold, then reconciles the hold to
its recorded usage. Unknown charges retain reservations. An interrupted run keeps
the hold conservatively; inspect before repeating. The parent job has an evaluation
status and cannot be claimed by normal workers. Real user tasks, progress, queue
contents and connector credentials are untouched.

The milestone does not complete live Docs/Gmail authorization, demonstrate time
savings, establish public-release readiness or guarantee future model outputs.
