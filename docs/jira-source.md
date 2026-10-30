# Jira Cloud selected issues

Jira has a confidential-web 3LO authorization flow, explicit authorized-site and
issue selection, immutable imports, manual checks and local disconnect. The UI
accepts an issue key or a canonical `/browse/KEY` link from the selected site.
Backend requests use the fixed Atlassian API gateway, never the pasted URL.

## Local setup (deferred)

Create an Atlassian developer OAuth 2.0 integration, add Jira API classic scope
`read:jira-work` and authorize `offline_access`. Prefer a site-restricted grant
where the developer console offers that option. Configure callback:
`http://127.0.0.1:8000/api/integrations/jira/callback`.

Set ignored local environment values `GHOSTTAB_JIRA_CLIENT_ID`,
`GHOSTTAB_JIRA_CLIENT_SECRET`, and the existing `GHOSTTAB_TOKEN_ENCRYPTION_KEY`.
The optional `GHOSTTAB_JIRA_REDIRECT_URI` must exactly match the registered
callback. Restart the API, connect from Connections, and consent when ready.
Never paste secrets into chats or commit them. Identity login is separate from
this source grant. For distribution, use the application's own 3LO integration;
users should not supply API tokens or create their own integration.

## Read and authorization boundaries

- Imports issue title, description and status only. No search, comments,
  attachments, writes or automatic synchronization. No assignee/deadline field is
  imported unless explicitly present in the description.
- Site access is freshly checked with `accessible-resources` before each import
  or manual check; the issue response remains authoritative for issue access.
  The site picker shows at most 50 sites. API site lists over 1,000 are rejected.
- Only standard `https://*.atlassian.net` site origins are supported. Custom-domain
  and government-cloud sites are deferred. Requests never follow redirects.
- Site membership changes rotate a local grant epoch, fence older in-flight
  reads, block saved issues from removed sites and preserve other authorized
  sites. Issue permission loss blocks that issue. Dependent briefs are hidden.
- Refresh-token rotation is serialized under the existing connection lock.
  Disconnect deletes local credentials and blocks sources/briefs; it does not
  revoke the application in Atlassian. Revoke there separately if desired.
- Transient failures preserve saved context. Manual checks discover permission
  changes; there is no claim of immediate remote revocation detection.
- Shared limits apply: eight active sources per task, 12,000 characters per source,
  20-second combined site/issue read deadline and 2 MB checked response size.

## Verified / pending

Provider-mocked API tests cover OAuth binding/replay, explicit site permission,
owner isolation, encrypted grants, rotation, duplicate import, immutable updates,
citations, failure handling, permission loss and disconnect races. The isolated
browser fixture exercises the frontend and real API using fictional responses.
Live app registration, consent and real Jira reads remain pending owner access.
Neither synthetic fixtures nor model trials prove a live Jira connection.

Protocol reference: [Atlassian 3LO documentation](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/).
