# Google Docs and Gmail: selected sources

October 31, 2026. The owner enabled Google Docs API, registered its callback,
completed real authorization and showed Connected in the normal app. The owner
then imported Docs alongside Calendar, prepared a brief, and reported the Docs
change/Check source/regeneration/citation sequence done. Screenshots show the
brief and Calendar citations; final Docs citation/update states still need an
independently captured demo record. See [current status](current-status.md).

Gmail remains implemented and simulated-provider tested but not live-connected.
The earlier October 28 mock/fixture results below remain distinct from this new
owner-run Docs verification. Live Docs disconnect/revocation and token-expiry
rehearsal are still pending.

## Workflow

1. Authorize Docs and Gmail separately in Connections when ready.
2. Open any workspace, including a Calendar workspace, and expand **Add Google
   Docs or Gmail context**. Paste a document link/ID, or search Gmail and explicitly
   select a message. Search returns up to five subject lines; refine the query if
   more results exist. Search results do not become persisted sources.
3. Import, inspect the source, then request preparation. Imports make no model
   calls; selected text can enter the existing Meta evidence packet on preparation.
4. **Check source** manually refreshes that selected resource. Changed content
   creates an immutable revision and makes the existing brief stale. Unchanged
   reads do not advance the generation. Missing/denied resources are blocked;
   transient failures preserve saved context. Source removal blocks dependent briefs.
5. Disconnect deletes the service's local credentials/pending authorization and
   blocks its imported sources/dependent briefs. Calendar and the other service
   remain separate. Reconnection does not restore removed items automatically.

No provider edits, sending, attachments, Drive browsing, background sync or source
discovery are implemented. Gmail imports one message, not its entire thread.
Docs extracts text, excluding images/comments. Existing eight-source/12K-character
limits apply, with an explicit incomplete-excerpt notice when truncated. Gmail's
original link may require switching to the authorized Google account.

## Setup for later authorization

Preserve the existing server-side Google client and encryption key. Enable Google
Docs API and Gmail API in the Google Cloud project, configure consent/test users,
and register these exact additional OAuth web-client redirect URIs. Keep the
existing Calendar redirect registered:

```text
http://127.0.0.1:8000/api/integrations/google/google_docs/callback
http://127.0.0.1:8000/api/integrations/google/gmail/callback
```

`GHOSTTAB_GOOGLE_SOURCES_CALLBACK_BASE` defaults to
`http://127.0.0.1:8000/api/integrations/google`; `/PROVIDER/callback` is appended.
Any future hosted setup needs a registered HTTPS callback base. The UI configured
indicator checks only local client/key presence, not Google API enablement,
registered callbacks, approved scopes or account eligibility.

Docs requests `documents.readonly`; Gmail requests `gmail.readonly`. These grants
provide account-level read permission, **not provider-enforced per-item access**.
GhostTab restricts actual reads to explicit search/import/refresh actions. Google
scope verification and Gmail restricted-scope/data-use requirements must be
reviewed before public release; this implementation does not establish compliance
or public OAuth approval. Credentials never enter the frontend or Meta.

Disconnect performs local credential removal/application blocking, not a Google
revocation call. Remove GhostTab in Google account permissions to revoke provider
authorization too. Immutable source revisions remain stored for provenance but
are not exposed as active sources or dependent snapshots after removal. Previously
copied/exported text cannot be recalled. External revocation is detected on later
token refresh or source reads, not continuously.

## Architecture and verification

Migration `0003` adds provider grants (`source_connections`), expiring single-use
browser/provider-bound PKCE state (`source_oauth_states`), and selected resource/
grant provenance (`source_references`). Existing Calendar tables are unchanged.
PostgreSQL browser roles have no direct table access. Run `npm run db:migrate`
before starting this version. The local database was backed up under ignored
`.ghosttab/backups` before the additive migration.

Owner and grant identity are checked before retrieval and again under a connection
lock before committing sources. Tests cover consent binding/replay/missing scope,
refresh/revocation, ownership, disconnect during import, duplicate imports,
immutable citation revisions, stale/blocked briefs, bounded Gmail metadata search,
and transient/missing-source handling. Required API CI, including PostgreSQL tests
and migrations, passed on the merged integration/catalog checkpoints.

The port-8010 browser fixture uses temporary storage, fake grants, MockTransport
and a fake model. A prominent banner identifies it; OAuth starts are disabled.
Browser verification covers document-link import, Gmail search/selection/import,
cited fake preparation, unchanged refresh and disconnect. The regular app is
**http://127.0.0.1:5173/** and shows Docs/Gmail as not connected until real consent.

Reference contracts: [Google OAuth](https://developers.google.com/identity/protocols/oauth2/web-server),
[Docs get](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/get),
[Gmail list](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list).
