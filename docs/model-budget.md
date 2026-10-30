# Meta inference and credit plan

**Teams milestone:** three real Spark calls added $0.033185 estimated usage.
The ledger totals $0.420940 including the retained Wonder reservation; the $1
application limit remains unchanged. Owner confirmation establishes promotional
credits in use; no billing settings were changed. No additional API key was needed.
See [Teams evaluation](teams-evaluation.md) for actual results and limitations.

**Jira milestone, October 29:** two Spark Jira/email trials added $0.017387
estimated usage. A Wonder code review failed with `model_output_incomplete`;
its $0.189828 reservation was conservatively retained, not reconciled to actual
usage. The cumulative ledger is $0.387755 including that hold, within the unchanged
$1 limit. No automatic retry. See [Jira evaluation](jira-evaluation.md).

**Later October 29:** two authorized Wonder comparisons added an estimated
$0.079264. Cumulative estimate: $0.180540. Model-aware rates/reservations now cover
Spark and Wonder; Spark remains the default. See [model comparison](model-comparison.md).

**October 29 checkpoint:** live synthetic inference has occurred. Five additional
cross-source evaluation calls used the existing worker and a $0.20 reservation
inside the unchanged $1 cumulative app budget. Returned usage estimated $0.048114
for those calls; see [evaluation report](meta-evaluation.md). The owner-supplied
billing screenshot showed promotional credits in use, but expiry and post-credit
overage behavior remain unconfirmed. The older planning text below is historical.

Updated October 26, 2026. The adapter and usage/reservation ledger are now implemented
and mock-tested. There has been no real inference or credit usage from this build.
The owner requires no charges during development. `GHOSTTAB_ALLOW_MODEL_REQUESTS`
defaults to false; verify credit-only use and provider billing controls before enabling it.

## Confirmed resources and current state

Harsh reports approved **$150 Meta Model API credits**. Treat that as the available
planning budget. The dashboard balance, expiration, eligible models, project
entitlements, and behavior after credits run out have not been independently
verified. Baseten $100, Modal $100, and Fireworks $25 remain approval-dependent;
the first release must work without them.

The repository has a server-side HTTP adapter, strict output/citation validation,
durable jobs, a cumulative usage ledger and atomic cost reservations. It makes one
request per attempt, with at most three attempts per source generation. API credentials,
actual account access, billing controls, live responses and estimates still need
verification. Planning, local UI use and mocked tests do not consume Meta credit.

## Model and interface decision

Use **`muse-spark-1.3` Standard mode** as the proposed default for task extraction,
context assessment, grounded briefs, conflicts, and drafts across work domains.
Keep **`muse-wonder-1.0`** as an explicit, bounded option after evaluation proves
that its additional capability improves a difficult case enough to justify cost
and latency. Do not route to it automatically because an output is uncertain.
Showing an unresolved question is a valid result.

Meta recommends Spark 1.3 for new work and lists tools, structured output, and
multimodal inputs for both model families. Wonder Full is not a Model API model.
Verify the actual accessible catalog before fixing configuration. [Meta models](https://dev.meta.ai/docs/models)

The proposed Python adapter lives behind an application interface such as
`prepare_brief(evidence, task, limits)`. The worker provides already-authorized
evidence; the adapter returns a typed result and usage metadata. Model responses
do not receive direct database or provider credentials and do not grant tool
authorization.

For the bounded, single-request MVP stages, prefer straightforward **Chat
Completions** with application-owned context. If Responses is needed, explicitly
use `store: false` and manage any replay deliberately. The API guide distinguishes
simple turns from workflows needing reasoning continuity and server-managed
history. GhostTab needs its own durable worker for ingestion, retrieval,
validation, retries, and refresh regardless of the model endpoint's background
execution support. [Responses API](https://dev.meta.ai/docs/protocols/responses)

Meta's base URL is **`https://api.meta.ai/v1`**, authenticated with a bearer key.
Its documentation uses `MODEL_API_KEY`, which now matches the repository's
commented environment example.
Load the secret only on the backend from an ignored environment file or hosting
secret store. An OpenAI-compatible client pointed at Meta calls Meta inference
and does not use OpenAI API billing. [Meta API reference](https://dev.meta.ai/docs/api-reference)

## First-call completion gate

Before declaring the model integration ready:

1. Verify dashboard credit balance, expiration, model eligibility, and overage
   behavior. Set available provider-side spending controls where supported.
2. Provision a dedicated project key through the normal dashboard flow; do not
   put it in chat, source control, browser variables, screenshots, or logs.
3. Check `GET /v1/models` using that key. Confirm the selected model rather than
   assuming public documentation proves account access.
4. Run one minimal synthetic request, followed by a small schema-constrained
   preparation. Capture usage, timeout behavior, errors, and actual billed cost.
5. Exercise the invalid-citation and budget-rejection paths before connecting
   private source content.

## Output contract and validation

Proposed structured fields are `task_title`, `summary`, `observed_facts`,
`evidence_ids`, `related_artifacts`, `decisions`, `conflicts`, `unknowns`,
`suggested_actions`, and `draft`. Each claim or action should carry supporting
evidence IDs; unavailable information stays explicitly unknown.

Use a flat Pydantic/JSON schema with required fields and closed objects. Chat
Completions uses `response_format`; Responses uses `text.format`. Meta documents
schema constraints and strict mode. [Structured output](https://dev.meta.ai/docs/structured-output)

Schema validity is separate from factual correctness. Application validation
must confirm that cited IDs exist in the authorized evidence set, quoted spans
match the stored source revision, related artifacts are supported, and no
unapproved action slipped into the result. Invalid output receives at most one
bounded repair opportunity; otherwise show a useful failure state. Never treat
a model-generated confidence number as measured reliability.

## Price baseline and a hypothetical preparation

Public Standard rates per million tokens are:

| Model | Uncached input | Cached input | Billed output |
| --- | ---: | ---: | ---: |
| `muse-spark-1.3` | $1.25 | $0.15 | $4.25 |
| `muse-wonder-1.0` | $4.00 | $0.20 | $20.00 |

These are public prices, not verified credit terms. [Pricing](https://dev.meta.ai/docs/pricing-rate-limits)

For an **aggregate 20,000 uncached input tokens and 4,000 billed output tokens
across a complete preparation**, arithmetic gives approximately **$0.042 for
Spark** or **$0.16 for Wonder**. One thousand identical preparations would cost
about $42 or $160. This is a planning example, not a benchmark. Extra calls,
retries, and hosted tools change the total.

Reasoning tokens count within billed output and the output limit. Include them
in the 4,000-token assumption rather than adding them a second time. Use modest
reasoning for extraction and increase it only when evaluation supports doing so.
[Reasoning and billing](https://dev.meta.ai/docs/reasoning)

## Application budget controls

The following are ceilings, not spending targets:

| Purpose | Ceiling |
| --- | ---: |
| Access checks and smoke tests | $10 |
| Development and prompt iteration | $40 |
| Evaluation and comparison | $40 |
| Demonstrations and recording | $20 |
| Reserved for failures and necessary follow-up | $40 |
| Total | $150 |

Reserve estimated worst-case cost atomically before each concurrent job. Base
that reservation on bounded input, maximum billed output, and remaining request
attempts; reconcile it against returned usage afterward. Persist model, request
ID, prompt/schema version, input/cache/output/reasoning token counts, latency,
validation status, and estimated cost. Reconcile estimates with the provider
dashboard and stop admissions before the balance is exhausted.

Start with two planned model calls and at most one additional repair or transient
retry: **three provider submissions per preparation in total**. Disable hidden
SDK retries so they cannot bypass that cap. Apply timeouts, limited concurrency,
rate-limit backoff, and task/source-revision deduplication. A timeout does not
prove that inference did not run or that a retry is free. No retry-charge or
exactly-once billing guarantee is assumed.

Store usage metadata, not raw private reasoning. Do not display or persist chain
of thought. Operational logs should omit source content and secrets by default.

## Privacy and optional providers

Standard mode states that content is not used to train Meta models. Contributor
variants exchange training permission for discounted usage; they are unsuitable
as the default for connected work content. Neither statement establishes Zero
Data Retention. [Pricing modes](https://dev.meta.ai/docs/pricing-rate-limits)

ZDR requires separate Meta enablement and has feature restrictions, including
background requests and stateful history. Do not claim it is enabled for this
account. [Meta ZDR documentation](https://dev.meta.ai/help/policies-and-privacy/zero-data-retention)

If other credits are approved, consider isolated open-weight model evaluation
against the same synthetic task set. Confirm eligible services and models first;
do not introduce GPU deployment merely to consume a credit. Private content
must never be automatically rerouted to another provider. Any later provider
change needs explicit product configuration, verified data handling, and fresh
quality and cost evaluation.
