# Web application

React and TypeScript interface, built with Vite. TanStack Query handles API state,
Supabase handles identity, and Zod validates responses. Run commands from the
repository root; see the [setup guide](../../docs/guides/setup.md).

| Area | Entry points in `src/` |
| --- | --- |
| Application and navigation | `main.tsx`, `App.tsx` |
| Account access | `AuthPanel.tsx`, `authActions.ts`, `accountSession.ts` |
| API contracts | `api.ts` |
| Connections | `ConnectorCatalog.tsx`, `catalogData.ts`, `GoogleSources.tsx`, `SlackSource.tsx`, `JiraSource.tsx`, `TeamsSource.tsx` |
| Workspaces and lifecycle | `WorkspaceList.tsx`, `TaskLifecycle.tsx`, `DraftEditor.tsx`, `draftState.ts` |
| Preparation and readiness | `ReadinessOverview.tsx`, `PreparationStatus.tsx`, `PreparationAccess.tsx`, `usePreparationReadiness.ts` |
| Source comparison | `SourceChanges.tsx`, `sourceDiff.ts`, `sourceLabels.ts` |
| Shared presentation | `styles.css`, `ThemeToggle.tsx`, `GhostMark.tsx`, `dates.ts`, `briefExport.ts` |

`tests/` contains Node-based regressions. `public/connectors/` contains local brand
assets and their attribution. Frontend configuration uses public `VITE_*` values;
never put service secrets there.

```sh
npm run dev
npm run check:web
npm run build
```

The default Vite proxy sends `/api` to the local backend. The built `dist/` folder
is generated and ignored; it is not a production deployment by itself.
