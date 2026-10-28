# Demonstration, evaluation, and showcase plan

Status: local walkthrough ready, October 27, 2026. No user-study or productivity result is claimed
by this document.

**Current build:** Google Calendar is the only confirmed account. The first
implemented local slice selects an event, adds clearly labeled manual notes,
prepares a cited brief when Meta is explicitly enabled, and checks source changes
manually. Live Calendar and synthetic Meta preparation are verified locally. See
[the repeatable walkthrough](demo-walkthrough.md). The multi-service story below
remains a release target requiring additional account authorization. Never present
manual notes as a live mail, chat or document integration.

## Future multi-service story

Use an authorized synthetic campaign approval or client handoff. A real test
email requests action, a shared document contains the work, and a Slack discussion
adds a decision or clarification. GhostTab assembles the task, explains source
relevance, identifies an unresolved question, and prepares an editable draft.
A subsequent document or message update changes the prepared context.

The sources may change to the owner's available Microsoft ecosystem before scope
freeze. Preserve the same task/evidence behavior. The preferred three-source story
depends on permissions working by Day 2; a complete two-service flow is acceptable.
Clearly identify every connector, manual import, fixture, and cached result.

## Three-minute video

| Time | Show | Purpose |
| --- | --- | --- |
| **0:00–0:20** | A concrete request and the scattered source context | Establish the person, task and avoidable preparation effort |
| **0:20–0:45** | Selected authorized sources and the real preparation trigger | Make the connection and task boundary understandable without spending the video on OAuth screens |
| **0:45–1:35** | Prepared workspace: cited brief, relevant excerpts, uncertainty, next step and editable draft | Demonstrate useful preparation and substantive Meta reasoning |
| **1:35–2:15** | A relevant source update, stale indication, preserved prior snapshot and refreshed context | Demonstrate a capability beyond a static summary |
| **2:15–2:45** | Measured result and a concise architecture explanation | Connect user benefit with source versions, durable jobs, model reasoning and deterministic validation |
| **2:45–3:00** | Product promise, demonstrated scope and next integration path | Explain the broader audience without claiming unbuilt capabilities |

Record actual behavior. Editing can remove waiting time if the transition is
disclosed; do not imply a cached workspace was freshly generated. Use synthetic
content through real authorized services so no employer or customer data appears.
A clearly labeled fixture replay is a recovery option, not evidence of a live
connection. Remove secrets and private source text from any public diagnostic trace.
Before recording and submission, check source grants, reconnect expired test
authorizations, and verify scheduled sync or any adopted push renewal. An initial
connection on Day 1 does not establish access through the deadline.

## Evaluation targets

Aim for **5–10 task trials across three scenarios** and a few prospective users,
including people outside software engineering. This is a target, not an existing
study. Scenario variations can cover campaign approval, client meeting preparation,
and operational handoff without adding new connectors.

Compare comparable manual/GhostTab tasks and counterbalance their order. Avoid
reusing an already-learned answer as the second task. Include checking and
correction time; record conditions, sample size and limitations.

| Measure | How to evaluate |
| --- | --- |
| Time to usable workspace | Start at task selection; stop when the user says they can begin, including verification/corrections |
| Citation integrity | Mechanically check that every citation ID resolves to the stored, authorized source revision |
| Claim support | Manually review whether the cited passage actually supports the claim; a valid ID alone does not establish correctness |
| Context quality | Label essential evidence missed and irrelevant evidence included |
| Freshness | Measure source-change detection and time until the replacement workspace is usable |
| Reliability | Record failed preparations, recoveries, duplicated jobs and visible stale/error behavior |
| Model use | Record input/output usage and estimated cost per prepared task using verified pricing |

Before recording, run a relevant change, an unrelated change, duplicate delivery,
model failure, worker restart, and revoked-access case. Verify that failures stay
visible and that source authorization applies during both retrieval and display.
Never turn a small sample into a universal percentage of work time saved.

## Submission and interview materials

Prepare a public README with capabilities, limitations, setup instructions,
screenshots and video. Test the clean-clone path and judge access instructions.
Offer an authorized read-only sample where practical so judges can evaluate without
connecting personal accounts or obtaining unpublished credentials.

Keep the architecture diagram and FAQ aligned with the code actually submitted.
Be ready to explain why the design uses a shared task/evidence model across roles,
why model calls run in durable jobs, how retries deduplicate, why snapshots preserve
source revisions, and how revoked access affects stored evidence. Explain both the
chosen solution and what would justify adding queues, search infrastructure or
more workers later. Separate implemented behavior from future design throughout.

The owner's supplied rubric gives impact **30%**, Meta AI tooling **25%**, technical
depth **20%**, and demo **25%**. These weights are transcribed from the supplied
screenshots, not independently verified. Allocate the showcase accordingly:
measured user benefit, a real Meta-backed step, visible engineering correctness,
and a rehearsed end-to-end demonstration. This plan improves the evidence available
to reviewers; it does not predict a prize or establish production readiness.
