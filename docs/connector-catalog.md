# Frontend integration catalog

The Connections page includes 49 tools across 14 categories from the owner's
broader product roadmap. The canonical list is `apps/web/src/catalogData.ts`.
Tools can belong to several categories but render only once in a result list.

Six entries map to existing connection flows: Google Calendar, Google Docs,
Gmail, Slack, Jira and Microsoft Teams. Cards read the existing owner-scoped
connection status queries and display Connected, Ready to connect, Setup required,
Checking status or Status unavailable. These labels do not establish provider
health or live verification. Manage opens the original provider controls.

The other 43 entries are **Planned** previews. Their detail view describes potential
context and explicitly states that connection/import is unavailable. They have no
Connect action, OAuth route, credentials, fake account status or imported sample
data. The catalog does not implement those integrations or promise delivery dates.
It is a frontend showcase, not evidence for a live-integration demonstration.

Search combines tool names, context descriptions and categories. Category and
availability filters combine; the grid initially shows 12 matching entries and
can reveal more. Existing connection options sort first. Empty results have a clear
reset action. Selection moves keyboard focus to details, and closing restores
focus to the originating card. Shared semantic tokens support both themes.

No backend endpoints, permissions, model calls or database migrations were added.
Provider-specific import flows inside workspaces remain unchanged. Existing
connection controls are reused rather than duplicated as alternate auth paths.
Switching between the Docs and Gmail detail panels remounts their controls so
temporary mutation/error state cannot carry over to a different provider.

October 31 local verification: `npm run check` passed 35 frontend tests, TypeScript,
ESLint, backend lint/format checks and 130 API tests. `npm run build` passed with
the existing large-bundle warning. The frontend checks/build passed again after
the provider-panel reset correction. PostgreSQL verification runs in PR CI.

## Loading issue found during development

A Windows case-insensitive module-name collision initially made Vite resolve the
catalog component to the similarly named data file. The data file was renamed to
`catalogData.ts`; type checks and production build passed. The running Vite server
retained the old resolved `.ts` path until restart. After restarting it, the served
App module imports `/src/ConnectorCatalog.tsx`, and that component serves HTTP 200
with the correct export. App, assets and API health were checked directly.

Use `http://127.0.0.1:5173/` for the real app. Port 8010 is the explicitly labeled,
isolated synthetic QA fixture, not the real account workspace. Browser automation
is currently unavailable, so visual and interactive browser verification remains
pending; do not claim that it passed. Unit/type/lint/build results are recorded in
the PR. The full source/backend CI gate is required before merge.
