# Selected Slack public threads

October 29, 2026. OAuth, encrypted grants, selection/import, manual refresh and
disconnect are implemented and mock-tested. **Live Slack installation and reads
are not verified.** No Slack credentials or real workspace authorization were
obtained. Calendar remains the only live-verified source connector.

## User flow and limits

Connect Slack in Connections when configured. Open a workspace, expand **Add a
Slack thread**, and paste a copied public-channel message link from the connected
workspace (`https://workspace.slack.com/archives/CHANNEL/pTIMESTAMP`). A copied
reply link with `thread_ts` selects its root thread. The browser extracts only
validated IDs; the backend never fetches the pasted URL.

The server checks channel metadata to reject private channels/DMs before retrieving
messages, even if a pre-existing Slack grant includes broader permissions. It reads
the first 15 messages and marks longer threads incomplete. It does not paginate,
read files, resolve member IDs, search the workspace, send messages or subscribe
to events. The original link opens the connected Slack channel rather than an
exact message permalink. Member IDs/Slack formatting may remain in source text.

Selected text becomes read-only evidence using existing immutable revisions and
citations. Imports do not run Meta; requesting preparation can send selected text
to Meta. **Check source** manually re-reads the selection. Changed content makes
an existing brief stale; loss of access blocks the source and dependent brief.
Rate limits/transient failures preserve context. External revocation is detected
on later explicit reads/refresh, not continuously. Local disconnect removes stored
credentials and blocks affected evidence; revoke the app in Slack as well if its
provider authorization should be removed. Immutable blocked versions stay in the
database but are excluded from active sources/derived snapshots. Exported copies
cannot be recalled.

## Server setup for later authorization

Configure a Slack confidential web OAuth app with user scopes `channels:read` and
`channels:history`, and set server-only `GHOSTTAB_SLACK_CLIENT_ID`,
`GHOSTTAB_SLACK_CLIENT_SECRET`, and `GHOSTTAB_SLACK_REDIRECT_URI`. The default
callback is `http://127.0.0.1:8000/api/integrations/slack/callback`; use the exact
redirect permitted/registered by Slack. Slack may require an HTTPS development
callback or an approved local configuration; local callback acceptance has not
been live-verified. No tunnel or public deployment is created by this milestone.
Preserve `GHOSTTAB_TOKEN_ENCRYPTION_KEY`; never put secrets in frontend variables.

The flow uses a client secret plus expiring, browser-bound, single-use OAuth
state tied to the GhostTab owner. It does **not** enable Slack public-client PKCE
mode, which is a provider-side one-way setting. No bot/write/private-message scopes
are requested. A returned user token and required scopes/workspace identity are
validated. Expiring user tokens are refreshed under the connection lock so single-use
refresh tokens are serialized; non-rotating credentials remain supported. Invalid
refresh/revoked tokens block the affected grant. Import publication checks grant
identity again under lock so a disconnect during retrieval cannot publish content.

The existing `source_connections`, `source_oauth_states`, and `source_references`
tables are reused; no new database migration or infrastructure is needed.

## Verification

API tests cover consent state/cookie replay, user-token/scope requirements, duplicate
selection, citations/staleness, private-channel rejection before message retrieval,
owner isolation, disconnect during read, rotating-token refresh and rate-limit/
revocation handling. Frontend tests reject untrusted/malformed selection links and
verify thread-root parsing. The 8010 fixture uses fake Slack grants/MockTransport;
its banner identifies simulated data and OAuth starts are disabled.

The browser rehearsal passed message-link import, cited fake preparation, unchanged
refresh and disconnect blocking. These are application workflow checks, not a live
Slack read or real Meta trial.

References: [Slack OAuth](https://docs.slack.dev/authentication/installing-with-oauth/),
[thread reads](https://docs.slack.dev/reference/methods/conversations.replies/),
[rotation](https://docs.slack.dev/authentication/using-token-rotation/),
[PKCE considerations](https://docs.slack.dev/authentication/using-pkce/).
