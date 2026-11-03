# Repository guide

The repository separates the application, documentation and developer tooling.
Runtime paths stay stable so existing local environments, imports and migrations
continue to work.

| Location | Contents |
| --- | --- |
| `apps/web/src/` | UI components, account/session state, API contracts and styling |
| `apps/web/tests/` | Frontend regression and fixture integration tests |
| `apps/web/public/connectors/` | Local brand SVGs, sources and attribution |
| `apps/api/src/ghosttab_api/` | API routes, authorization, sources, persistence and preparation |
| `apps/api/migrations/` | Versioned schema changes |
| `apps/api/tests/` | Isolated API tests, provider simulations and evaluation fixtures |
| `docs/` | [Topic-based documentation](README.md) |
| `scripts/` | Cross-platform backend launcher and documentation-link checker |
| `.github/` | Required CI and PR template |
| `.ghosttab/` | Ignored local data, screenshots, backups and recovery notes |

Use the [frontend guide](../apps/web/README.md) or
[backend guide](../apps/api/README.md) to find the relevant modules.

## Names and changes

Use lowercase, hyphenated branch names describing the work:

- `feat/source-change-review` for new behavior.
- `fix/session-and-connection-recovery` for corrections.
- `docs/setup-guide` for documentation.
- `chore/repository-organization` for maintenance.

File names follow their existing language conventions: React components use
PascalCase, TypeScript utilities use camelCase, Python modules use snake_case,
and documentation uses descriptive hyphenated names.

Create a focused branch from current `origin/main`, review the diff, run relevant
checks, and merge through the protected PR workflow. Describe what changed and
how it was verified. Preserve authorship, source attribution and historical
evidence; naming cleanup does not rewrite commits. See [Contributing](../CONTRIBUTING.md).

## Local recovery files

Previous local handoff notes and the empty dump file were preserved under
`.ghosttab/repository-cleanup-20261102/`; they are not submission artifacts.
The directory also records pre-cleanup branch references and document moves.
Never delete `.ghosttab/` as a general cleanup: it contains the working database.

The public recovery entry point remains [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md).
