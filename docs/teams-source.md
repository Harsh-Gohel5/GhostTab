# Microsoft Teams selected chats

Teams has a read-only connection, explicit chat import, manual check and local
disconnect flow. It reuses encrypted source grants and immutable evidence; no
database migration or new infrastructure. **Live consent and reads are pending.**

## Deferred local setup

Register a confidential web application in the work/school Microsoft Entra tenant.
Use single-tenant accounts, the Microsoft Graph **delegated** `Chat.Read` permission,
and OAuth `offline_access`. Tenant policy can require administrator consent. No
application-wide read permission, message sending or personal Microsoft accounts.

Register Web callback `http://127.0.0.1:8000/api/integrations/teams/callback`.
Set ignored local environment values `GHOSTTAB_TEAMS_TENANT_ID` (tenant UUID),
`GHOSTTAB_TEAMS_CLIENT_ID`, `GHOSTTAB_TEAMS_CLIENT_SECRET`, plus the existing
`GHOSTTAB_TOKEN_ENCRYPTION_KEY`. Optional `GHOSTTAB_TEAMS_REDIRECT_URI` must match
the callback. Restart the API, then connect when ready. Never commit credentials.
Source consent is separate from GhostTab account login.

## User workflow and limits

From a workspace, expand **Add a Teams chat**. Enter an existing chat ID such as
`19:…@thread.v2`, or its `https://teams.microsoft.com/l/chat/…/conversations` link.
The equivalent `teams.cloud.microsoft` host is supported. Channel links, new-chat
links and message permalinks are not supported in this slice; use a chat ID instead.
Only the validated ID reaches the backend; query context and arbitrary URLs do not.

- Reads the selected chat metadata and latest page of at most 50 messages through
  fixed Graph `/me/chats` endpoints. Explicit descending creation order is reversed
  for chronological display. No chat browsing, channels, attachments or writes.
- Imported text retains sender and source creation time when provided. Deleted
  messages and system events are omitted. HTML becomes text, never executable UI.
- Older pages are not followed. A next-page marker or text truncation produces an
  incomplete-excerpt notice. Shared limits: eight active sources, 12,000 characters
  each, 20-second combined read deadline, 2 MB checked response size; redirects off.
- `Chat.Read` grants access to the user's chats more broadly than a selected item.
  GhostTab retrieves only the chat explicitly imported or checked. Selected text
  can reach Meta when preparation is requested.
- PKCE and a single-use owner/browser-bound state protect the callback. Tokens are
  encrypted; refresh is serialized by the existing connection lock. The configured
  tenant is fixed to a UUID and changing it requires reconnecting.
- Ownership and connection identity are checked before reads and again at commit.
  Disconnect during retrieval cannot publish the result. Missing access blocks
  saved chat evidence and dependent briefs; 401 blocks the connection's sources.
  Transient failures preserve context. Empty text after deletion blocks old text.
- Disconnect deletes local credentials and blocks evidence/briefs; it does not
  revoke the app in Microsoft. No automatic synchronization or immediate remote
  revocation detection is claimed. National-cloud endpoints are not supported.

## Verification

Mocked API tests cover PKCE/state replay, required scope, owner isolation, encrypted
grants, token refresh, tenant changes, duplicate import, citations, immutable
updates, empty/malformed text, transient errors, permission loss and disconnect
races. Browser rehearsal passed import, cited fake preparation, unchanged manual
check and disconnect blocking. Real tenant registration/consent and reads remain
unverified. Synthetic tests do not establish live integration.

Primary references: [authorization code/PKCE](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow),
[get chat](https://learn.microsoft.com/en-us/graph/api/chat-get?view=graph-rest-1.0),
[list chat messages](https://learn.microsoft.com/en-us/graph/api/chat-list-messages?view=graph-rest-1.0).
