# Credential-free connector milestone

**October 31 update:** this file retains the earlier adapter/fixture milestones.
The complete provider flows and catalog are merged. Calendar and Docs now have
owner-run live evidence; Gmail, Slack, Jira and Teams still need live account
verification. See [current status](current-status.md) and
[Google sources](google-sources.md). Statements below about deferred Docs consent
or unmerged work describe their dated historical checkpoint.

**Teams checkpoint:** selected-chat connection/import/refresh/disconnect now has
UI/API flow with simulated provider verification. All five additional readers now
have corresponding connection flows; live Docs/Gmail/Slack/Jira/Teams consent is
still pending. Calendar remains the sole live-verified connector. See [Teams](teams-source.md).

**Jira checkpoint, October 29:** selected-issue 3LO connection, explicit site
selection, import, manual refresh and disconnect are implemented. The normal UI
shows setup pending until the owner configures Jira. Mock API and isolated browser
checks passed; no live consent or real Jira reads. See [Jira](jira-source.md).
Calendar remains connected with five existing local workspaces. Teams is the next
connector milestone; live additional-source and hosted identity gates remain.
New work is committed/pushed on the feature branch; main remains unchanged.


**Slack update:** public-thread connection/import/refresh/disconnect UI/API now
exists and reuses the source-grant tables. It is mock-tested, not live-authorized.
Private channels/DMs are excluded. See [slack-source.md](slack-source.md). The older
adapter-only description below now applies to Jira/Teams.

**Later October 28 update:** Docs/Gmail now have frontend and backend connection,
selection, import, refresh and disconnect flows with an additive schema migration.
They are tested with simulated providers; no live authorization has occurred. See
[google-sources.md](google-sources.md). The adapter-only description below remains
the earlier checkpoint and still describes Slack/Jira/Teams. The test app now has
a prominent synthetic banner and simulated Docs/Gmail grants for UI verification.

October 28, 2026. Account connections are deferred at the owner's request. Calendar
remains the only live-verified connector. This milestone does not expand its scopes,
store new credentials, change the database schema or authorize private source reads.

## Implemented and mock-verified

| Reader | Explicit selection | Extracted text |
| --- | --- | --- |
| Google Docs | Document ID | Body, tabs, nested tabs and table text |
| Gmail | Message ID | Plain text preferred, HTML fallback; attachments excluded |
| Slack | Channel ID and thread timestamp | First bounded page of replies; incomplete threads labeled |
| Jira Cloud | Cloud ID and issue key | Summary, status and description text |
| Microsoft Teams | Chat ID | First bounded page of non-deleted messages; HTML/plain text distinguished |

`connector_adapters.py` uses fixed HTTPS provider endpoints, validated identifiers,
one GET per selected source, disabled redirects, timeouts, bounded extracted text,
safe error codes and explicit incomplete-excerpt notices. It accepts an injected
HTTP client so tests need no secrets or network. It does not follow links, download
attachments, execute source instructions, send messages or modify providers.

These are reader adapters, not complete production connectors. They have no public
import routes or OAuth UI. Before live wiring, the server must validate the owner,
the provider/resource grant and selected resource both before retrieval and before
publication, and supply an appropriately authorized server-owned client. Normalized
source data is never proof of authorization. User-supplied tokens/URLs are not an
authentication mechanism. Provider-specific OAuth, scope/consent, token refresh,
disconnect/revocation and persisted provider-resource identity are still pending.

## Shared workflow verification

Synthetic responses for all five readers enter a disposable owner-scoped workspace.
The existing preparation worker validates a fake multi-source brief with exact
quotes. Tests verify citation revisions, stale marking on update, blocking the
derived brief on source removal and rejecting another owner's access. No Meta or
provider calls are made. Live correctness and provider authorization are unverified.

Run `npm run build`, then
`.venv/Scripts/python.exe apps/api/tests/browser_fixture.py`, and open
`http://127.0.0.1:8010`. This uses a temporary database and a fake model. Source cards
say SYNTHETIC … SAMPLE · NOT CONNECTED; the brief explicitly identifies itself as a
synthetic rehearsal. The normal app, Calendar grant and private data are untouched.

## Next dependency gates

Checkpoint verification: `npm run check` passes TypeScript, ESLint, 19 frontend
tests, Ruff and 54 API tests. `npm run build` and `git diff --check` pass. Browser
rehearsal confirmed all five synthetic provider labels and a multi-source fake
brief. Existing bundle-size/Alembic warnings remain. No PR has been created.

1. Configure separate provider grants without disturbing Calendar; implement explicit
   resource selection and attachment/refresh using the existing evidence revisions.
2. Add Docs/Gmail live authorization once the owner is ready. Keep selected resources
   bounded and consent specific. Mail/Docs permissions are not included in Calendar.
3. Verify Slack/Jira installations and a supported Microsoft work/school tenant.
4. Ship a connector only after real authorized read, source-change, revoked-access
   and isolation checks pass. Mock adapters must not be advertised as live services.

Reference API contracts: [Docs](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/get),
[Gmail](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get),
[Slack](https://docs.slack.dev/reference/methods/conversations.replies/),
[Jira](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro),
[Teams](https://learn.microsoft.com/en-us/graph/api/chat-list-messages?view=graph-rest-1.0).
