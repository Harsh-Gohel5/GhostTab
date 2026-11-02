# Frontend integration catalog

November 1 UI refinement: all 49 tools appear as compact logo tiles, with local
SVG assets and per-file provenance in `apps/web/public/connectors/SOURCES.json`.
Selecting a tile opens its existing connection controls in a modal dialog.
The gallery adds no backend endpoints, credentials, permissions or dependencies.
The follow-up organizes the gallery into two pages of 25 and 24 tools, with five
aligned desktop columns and previous/next/page controls. Every tile says
**View options**; connected status remains available through the status dot,
accessible label, filters and details.

October 31: catalog [PR #12](https://github.com/Harsh-Gohel5/GhostTab/pull/12) is
merged as `c8e360a`; required web/API CI passed, including PostgreSQL tests and
migrations. Owner screenshots now show the dark catalog and Google Docs Connected,
and the owner completed connection management through the normal app. At that
checkpoint, filter/focus/responsive verification remained pending. See
[current status](current-status.md) for the later live workflow.

The Connections page includes 49 tools across 14 categories from the owner's
broader product roadmap. The canonical list is `apps/web/src/catalogData.ts`.
Tools can belong to several categories but render only once in a result list.

Six entries map to existing connection flows: Google Calendar, Google Docs,
Gmail, Slack, Jira and Microsoft Teams. Tiles read the existing owner-scoped
connection status queries; details display Connected, Ready to connect, Setup required,
Checking status or Status unavailable. These labels do not establish provider
health or live verification. Selecting a tile opens the original provider controls.

The other 43 entries remain unavailable integrations. Each detail view has a
**Connect to [app]** action and states that account access/import is unavailable
in this release. Clicking shows availability feedback; it does not redirect,
request credentials, create grants or mark an account connected. These entries
have no OAuth route or imported sample data. The catalog does not implement those
integrations or promise delivery dates.
It is a frontend showcase, not evidence for a live-integration demonstration.

Search combines tool names, context descriptions and categories. Category and
availability filters combine. Quick filters show all tools, the six connection
options, connected tools or planned entries. Search/filter changes return to page
one; the current page is clamped when live statuses change. Existing connection
options sort first. Page navigation returns focus and scroll to the tile grid.
Empty results have a
clear reset action. The native modal traps keyboard focus, supports Escape, locks
background scrolling and restores focus to the originating tile on close.
Shared semantic tokens support both themes; narrow screens use three tile columns.

No backend endpoints, permissions, model calls or database migrations were added.
Provider-specific import flows inside workspaces remain unchanged. Existing
connection controls are reused rather than duplicated as alternate auth paths.
Switching between the Docs and Gmail detail panels remounts their controls so
temporary mutation/error state cannot carry over to a different provider.

October 31 local verification: `npm run check` passed 35 frontend tests, TypeScript,
ESLint, backend lint/format checks and 130 API tests. `npm run build` passed with
the existing large-bundle warning. The frontend checks/build passed again after
the provider-panel reset correction. PostgreSQL verification runs in PR CI.

November 1 local verification: required checks passed 50 frontend tests and 142
API tests; the production build passed with the existing large-bundle warning.
After the keyboard-focus correction, frontend checks and the build passed again.
Browser verification used only the existing disposable synthetic fixture on 8010:
all 49 logos loaded; all six existing provider panels opened; search, combined
filters, empty-result reset, planned previews, keyboard navigation, Escape and
focus restoration passed. Desktop dark/light themes and a 390px phone viewport
were inspected, with no horizontal overflow. This verifies UI behavior, not fresh
live OAuth or provider health. No demo data or environment configuration changed.

Two-page follow-up verification: `npm run check` passed 51 frontend tests and
142 API tests; `npm run build` passed with the existing bundle warning. Disposable
browser checks confirmed 25 + 24 unique entries, View options on every tile,
page navigation, search from page two, availability feedback with no redirect,
focus restoration and a 390px phone layout without horizontal overflow. Slack
disconnect and the resulting Connect to Slack control were checked only against
the synthetic fixture; no real account grants were changed.

## Loading issue found during development

A Windows case-insensitive module-name collision initially made Vite resolve the
catalog component to the similarly named data file. The data file was renamed to
`catalogData.ts`; type checks and production build passed. The running Vite server
retained the old resolved `.ts` path until restart. After restarting it, the served
App module imports `/src/ConnectorCatalog.tsx`, and that component serves HTTP 200
with the correct export. App, assets and API health were checked directly.

Use `http://127.0.0.1:5173/` for the real app. Port 8010 is the explicitly labeled,
isolated synthetic QA fixture, not the real account workspace. Browser automation
was unavailable at the October 31 checkpoint; the November 1 fixture checks above
supersede that UI verification gap. Live provider restrictions remain unchanged.
