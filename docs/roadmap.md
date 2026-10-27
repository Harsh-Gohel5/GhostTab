# Hackathon delivery roadmap

Planning baseline: October 26, 2026. Harsh is building solo for approximately
6–8 hours per day. Eight build days through November 2 provide roughly 48–64
hours; November 3–4 are reserved for recording, submission, and repairs.

**Implementation update, Oct 26:** Google Calendar is the only account currently
confirmed by the owner, and is the first connector. The local slice now includes
task/evidence persistence, manual notes, source revisions, preparation jobs/worker,
Meta and Calendar adapters, and Today/Workspaces/Connections. Provider flows are
mock-tested; live OAuth and inference are pending. Development must remain local
and free, and Meta requests are disabled until credit/billing verification. The
broader audience and eventual cross-tool product remain unchanged. The two-service
release gate below still needs an additional authorized source; do not imply that
one calendar plus manually added notes already proves two live integrations.

## Release promise

GhostTab prepares a task workspace for people whose work crosses messages,
documents, meetings, and task systems. A user should be able to inspect the
request, relevant evidence, unresolved questions, and a prepared next action,
then see when a source update changes that context. Engineering is one optional
workflow within this broader audience.

The required release demonstrates one authentic connected workflow across at
least two services, real Meta reasoning, traceable sources, and a relevant-source
update. Three sources are the preferred target, conditional on permissions
working by Day 2. Editable draft review is sufficient; automatic external sending
is outside the required scope.

## Known status and dependencies

- **Done:** public repository, React/TypeScript/Vite interface, FastAPI health
  endpoint, documented local setup, dependency locks, six passing API tests, and
  passing initial frontend/backend CI jobs.
- **Confirmed by the owner:** $150 in Meta Model API credit. Public Meta models,
  endpoint and pricing have been checked; account-specific model eligibility,
  credit expiry, actual limits, balance and overage behavior still need checking.
- **Unconfirmed:** Baseten $100, Modal $100, and Fireworks $25 approvals. The release
  must work without these credits.
- **Account choice:** Google Calendar only is confirmed for the first connector.
  Google OAuth configuration and live consent are pending. Mail, document and chat
  authorization is not available yet. Keep task/evidence modules provider-independent.

## Eight-day sequence

| Day | Focus | Completion gate |
| --- | --- | --- |
| **1 · Oct 26** | Freeze a nontechnical scenario; verify Meta access and test-account authorization | One real model call succeeds; permitted sources and test users are identified; expected brief, evidence and update behavior are written down |
| **2 · Oct 27** | Identity, PostgreSQL migrations, a minimal job worker and a thin vertical slice; deploy the skeleton early | An authorized source item reaches persistent storage, an asynchronous model-backed preparation reaches the UI, and the protected cloud skeleton works; source-permission feasibility is resolved |
| **3 · Oct 28** | Complete the chosen sources, bounded scheduled sync and evidence association | Preferred three-source flow works through explicit links, thread IDs and user selection; provenance and relevance are visible; user can remove an irrelevant item |
| **4 · Oct 29** | Harden worker recovery, bounded retries, validation and draft review | Jobs survive restart; retries do not create duplicate workspaces; malformed output or invalid citations fail visibly; draft remains editable and unsent |
| **5 · Oct 30** | Freshness, revocation and recovery | Relevant changes invalidate snapshots; unrelated changes do not; old snapshot survives refresh; revoked sources stop being used or displayed; failure/retry states are inspectable |
| **6 · Oct 31** | Calm onboarding and complete workspace interactions | Today, Workspaces and Connections work; source selection and synchronization status are clear; keyboard, narrow-screen, loading, empty and error states are checked |
| **7 · Nov 1** | Evaluation and delivery hardening | Authorization isolation, source updates and clean-clone setup pass; small comparative trials are recorded; cloud setup and judge access instructions are reproducible |
| **8 · Nov 2** | Feature freeze and showcase preparation | Critical fixes only; demo rehearsed and recorded; repository documentation, architecture explanation and submission packet ready |

Build the interface with each working slice. Day 6 finishes interactions; Day 7
hardens the deployment established on Day 2.

## Scope gates and cut lines

Time-box a failing connection investigation to approximately half a build day,
then choose an authorized path that supports the demonstration. Additional
integrations wait until the primary flow is complete.

If three sources are not feasible by Day 2, freeze a two-service connected flow.
Manually supplied text, links, or files can keep the product useful, but must be
visibly labeled as imports; they do not establish a live connector. Demonstrate
freshness only for a source whose update mechanism actually works.

The first task trigger may be explicit selection, a chosen label, or an approved
preparation rule. Broad autonomous discovery of every responsibility is optional.
Begin associations with explicit links and IDs; uncertain model associations need
an explanation and a correction mechanism.

Start synchronization with bounded scheduled polling and persisted cursors. Add
provider push/webhooks only when the preparation and freshness gates pass.
Google external OAuth apps in Testing have a seven-day refresh-token expiry
except identity-only scope cases; an early connection may therefore need
reauthorization before submission. Rehearse reconnect before recording and check
again before submitting. If Gmail push is adopted, renew its watch at least every
seven days; Google recommends daily renewal. See [Google OAuth token expiry](https://developers.google.com/identity/protocols/oauth2/)
and [Gmail push renewal](https://developers.google.com/workspace/gmail/api/guides/push).

Calendar is optional if meeting preparation becomes the primary story. Jira,
GitHub, Microsoft as an additional ecosystem, and other catalog entries wait
until the release gates pass. A local Git bridge, execution sandbox, automatic
publishing, vector search, Kafka, and a general DAG engine are outside this build.
The target is a credible prototype with clear limitations, not production readiness.

## Credit and hosting discipline

Suggested Meta spending ceilings: $10 access checks, $40 development, $40 evaluation,
$20 rehearsal/demo runs, and $40 reserve. These are allocations, not cost forecasts.
Verify pricing and credit terms before translating dollars into tokens.

Track usage and estimated cost per job. Bound input excerpts, output length,
concurrency, retries, and daily use; reuse unchanged evidence and snapshots.
Use optional provider credits for a demonstrated need after approval.

Inference and hosting budgets are separate. Check hosting/database plans and limits
before selection. No paid service purchase is authorized by this roadmap.

## Submission window

The owner's supplied kickoff screenshots state a build window of October 26–
November 4, 2026, a public repository, teams of up to four, and submission through
the event platform with a three-minute video. The supplied deadline is
**November 4 at 9:00 PM ET, equivalent to 7:00 PM in Phoenix**. These event details
have not been independently verified here; check the organizer's final instructions.

Target a complete submission on November 3. Preserve November 4 as contingency,
not an extra feature day. See [demo-plan.md](demo-plan.md) for the evidence and
showcase plan.
