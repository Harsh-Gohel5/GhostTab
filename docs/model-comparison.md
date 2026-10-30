# Spark and Wonder comparison

October 29, 2026. A read-only request to the authenticated Meta model catalog
returned `muse-wonder-1.0` and `muse-spark-1.3`, among other IDs. It did not list
Wonder Full. Meta documents Wonder Full as subscription-only in Muse Code, not
a Model API variant. No subscription or installation was purchased or enabled.

Two real Wonder requests repeated the fictional conflict and missing-owner cases
from the Spark evaluation, with the same `meeting-brief-v2` prompt and low reasoning.
Both passed schema/quote checks and the coding agent's narrow expectation review.
This is a tiny, uncontrolled comparison, not a general model ranking.

| Case | Spark latency / estimate | Wonder latency / estimate |
| --- | --- | --- |
| Conflicting deadlines | 8.27 s / $0.009942 | 14.73 s / $0.039340 |
| Missing owner | 9.28 s / $0.011220 | 35.80 s / $0.039924 |

Both models preserved conflicting dates and missing ownership. Wonder emitted raw
evidence IDs/quotes inside some unknown strings in one case, reducing presentation
quality. It did not demonstrate a clear advantage on these cases. **Spark remains
the unchanged application default.** Wonder is an explicit server configuration/
evaluation option, not automatic escalation or an invented “better” UI setting.

Budget reservation/reconciliation is now model-aware. Standard per-million-token
rates used are Spark input $1.25, cached input $0.15, output $4.25; Wonder input $4,
cached input $0.20, output $20. Unknown models fail rather than using Spark rates.
The two Wonder calls added $0.079264 estimated usage; cumulative app estimate is
$0.180540 after this comparison. The $1 cumulative limit is unchanged. These are
application estimates, not provider billing confirmation. All source material
was fictional. No private source data was sent.

[Sanitized Wonder outputs/token usage](evaluations/wonder-2026-10-29.json) complement
the [Spark report](meta-evaluation.md). After explicit authorization, reproduce with
`.venv/Scripts/python.exe apps/api/tests/evaluate_meta.py --live --model muse-wonder-1.0 --cases conflict missing_owner`.
The existing $0.20 global hold/disposable-worker budget mechanism applies. Do not
repeat paid inference merely to inspect the report. No other model family was
added: transcription/image generation/segmentation need a concrete product use.

Sources: [Meta model availability](https://dev.meta.ai/docs/models),
[Meta rates](https://dev.meta.ai/docs/pricing-rate-limits).
