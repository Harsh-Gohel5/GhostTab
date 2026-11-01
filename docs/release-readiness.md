# Release-readiness rehearsal

November 1, 2026. Failure testing uses disposable storage, not the signed-in demo.
Existing baseline: 42 frontend tests, 136 API tests and production build passed.

## Isolated authentication fixture

Run `.venv/Scripts/python.exe apps/api/tests/auth_browser_fixture.py` and open
`http://127.0.0.1:8011/`. It serves the built frontend with a temporary database.
Use `demo@example.test` or `other@example.test`, both with `demo-password`.
The identities, tokens and endpoints are fictional. No real provider is contacted.
The fixture verifier is not installed in the production application.

The fixture-only `POST /synthetic/scenario` accepts `logout_failure` (boolean),
`refresh_failure` (`none`, `rejected`, `temporary`) and `tasks_delay_ms` (0–5000).
Omitted values reset to defaults. These controls exist only in the disposable
fixture; never add them to the normal API. Refresh tokens identify their owner.
The fixture does not model provider-side access-token revocation after logout.

Fixture tests verify two-owner task isolation and bounded, recoverable failure
controls. Browser sign-out, session restoration, account-switch races and live
Calendar/Docs recovery remain separate acceptance checks.

## Calendar replacement-grant correction

A regression reproduced both an old refresh rejection and an old read rejection
disconnecting a newly connected Calendar grant. Automatic disconnect now checks
the failed request's grant identity under the connection lock. Explicit user
disconnect remains unconditional. Targeted Calendar/OAuth checks passed (5 tests),
including preservation of newly imported evidence after a replacement grant.
