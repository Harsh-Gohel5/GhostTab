# Current development checkpoint

October 31, 2026, America/Phoenix. This is the current public handoff. Older dated
checkpoints elsewhere describe their state at the time; use this page for the
latest verification boundary. No account identifiers, private source contents,
credentials or browser sessions are included.

## Product and implementation

GhostTab brings selected evidence from work tools into a task workspace, prepares
a cited brief and editable unsent draft through Meta, and marks the saved context
stale when a manually checked source changes. It serves people working across
messages, documents, meetings and tasks. General autonomous discovery, automatic
external sending and continuous synchronization are not implemented.

The existing React/TypeScript frontend, FastAPI API, separate durable worker and
SQLAlchemy/Alembic storage remain in place. Development uses local SQLite and
Supabase identity; PostgreSQL behavior and migrations are exercised in CI, not
evidence of a deployed database. Migration head is `0004`. Provider credentials
stay encrypted on the backend. Google identity and connector grants are separate.

Implemented features include task/evidence persistence, immutable source versions,
manual notes, preparation recovery, exact-quote validation, source-generation and
worker-lease publication checks, model usage reservations, concurrent draft-save
protection, readable dates, copy/Markdown export, review/completion/reopening,
workspace search and readiness filters, light/dark themes, finite ghost greetings
and profile initials.

Connections lists 49 tools in 14 categories. Calendar, Docs, Gmail, Slack, Jira and
Teams reuse implemented connection flows. The other 43 are visibly Planned
previews with no authorization/import behavior or fake account data.

## Live workflow evidence

| Capability | Latest evidence and boundary |
| --- | --- |
| Email signup, confirmation and sign-in | Owner confirmed successful use against the real configured Supabase project. |
| Google identity sign-in | Owner confirmed successful use after provider configuration; the real provider settings/authorization redirect were also checked. |
| Signed-in workspace actions | Owner screenshots show a signed-in profile, selected Calendar import, saved context and a prepared brief. This is workflow evidence, not a new security audit. |
| Calendar | Previously live-verified; the owner reconnected it for the signed-in account, listed an upcoming event and imported it. |
| Google Docs | Owner enabled the API, registered the existing connector callback, completed consent and showed Connected in the catalog. Document import was then performed through the normal workspace UI. |
| Calendar + Docs preparation | Owner followed the two-source import/preparation sequence and reported it working. Screenshots show the generated brief, cited Calendar assertions and an editable draft. They do not independently show the final Docs citation. |
| Docs change and regeneration | Owner replied “done” after instructions to add a unique fictional ownership fact to the Doc, Check source, observe Update needed, regenerate and inspect a Docs citation. Record this as owner-reported completion; final source quotes and update states were not independently captured by automation. |
| Gmail | Implemented and mock-tested, but the latest screenshot explicitly showed not connected. No live Gmail read is claimed. |
| Slack, Jira and Teams | Connection/import/manual refresh/disconnect implemented and tested with simulated providers; live account authorization remains pending. |

The demonstration uses fictional content in actual Google resources. It is a live
connector workflow with test content, not evidence of real customer adoption or
measured productivity gains. The first two-service workflow is owner-reported
complete; independent capture of both source citations and the before/after
refresh sequence is still required for the final demo record.

## Verification and Git checkpoints

All application changes through the catalog are already on protected `main`:

| PR | Main commit | Scope |
| --- | --- | --- |
| [#9](https://github.com/Harsh-Gohel5/GhostTab/pull/9) | `9566791` | Additional source flows, account UI, task progress and accumulated integration work. |
| [#10](https://github.com/Harsh-Gohel5/GhostTab/pull/10) | `43dc01b` | Grounding correction, targeted live Meta evaluation and retained failure evidence. |
| [#11](https://github.com/Harsh-Gohel5/GhostTab/pull/11) | `b1be945` | Google identity-provider readiness and safe retry guidance. |
| [#12](https://github.com/Harsh-Gohel5/GhostTab/pull/12) | `c8e360a` | Searchable connector catalog, explicit Planned previews and provider-panel state isolation. |

The catalog checkpoint passed `npm run check`: 35 frontend tests, TypeScript,
ESLint, backend lint/format checks and 130 API tests. The production build passed;
the existing large-bundle warning remains. Frontend checks/build passed again
after the Docs/Gmail panel correction. PR #12's required web/API CI passed,
including the API suite on PostgreSQL and migration upgrade. Existing Alembic
deprecation warnings remain. These results do not establish production readiness.

This documentation checkpoint changes no runtime code or dependencies. Its own
PR must pass the same required CI before merge. Branches, commits and focused PRs
remain mandatory; merge through GitHub, then fast-forward local main.

## Local operation and current limitations

- Real app: `http://127.0.0.1:5173/`; API: port 8000. Port 8010 is an explicitly
  synthetic isolated fixture, not the real account workspace.
- Chrome loads the app. The Codex embedded browser loaded a public test page but
  failed to load both local hostnames and the API health page. Browser automation
  also timed out. The cause is unresolved; it is not a verified GhostTab bug.
- A Windows loopback exemption was proposed as a diagnostic; the user reported no
  improvement and was instructed to remove it. Removal was not independently
  confirmed. Do not add security exceptions or claim this troubleshooting fixed it.
- Calendar and Docs connect separately for each application identity. Old local
  owner data/grants are preserved and are not silently migrated into a signed-in
  account. Import both items into the same workspace to test two-source preparation.
- Supabase recovery/password update, broad email delivery, reconnect/expiry and
  signed-in account isolation still require final live rehearsal. Existing automated
  authorization tests are distinct from those owner-run tests.
- No external deployment or paid hosting is authorized or performed. Judge access,
  clean-clone rehearsal, video and final submission remain unfinished.

## Meta use and next priorities

Spark 1.3 remains the default. Bounded Wonder comparisons did not show a clear
benefit on the evaluated cases. `meeting-brief-v3` and exact source quotes are
retained. Historical trials and costs are in [grounding evaluation](grounding-evaluation.md)
and [model comparison](model-comparison.md); they are not a broad accuracy score.

The owner has confirmed promotional-credit use and authorized useful bounded
inference. The last checked local application cap is still $1; no increase was
made. New owner-triggered demo calls have not been reconciled into a new public
ledger total here. No extra keys or calls are needed to publish documentation.
Do not confuse Meta usage with the coding assistant's separate token usage.

Next, capture the two-source evidence/update flow and check semantic support;
then address issues found in recovery, account isolation, reconnect and final demo
rehearsal. Prioritize a reliable task/context-change lifecycle over more planned
tiles. Finish accurate setup/judge access instructions, the video and submission
packet before adding optional scope. See [demo walkthrough](demo-walkthrough.md)
and [roadmap](roadmap.md).
