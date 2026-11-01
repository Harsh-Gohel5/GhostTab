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
Preparation in this fixture uses an explicit fake model, allowing signed-in draft
checks without an inference key or live request. The normal Meta adapter is never
used. To run the optional actual-SDK integration check while the fixture runs:
`node --experimental-strip-types --test --test-timeout=15000 apps/web/tests/sessionFixture.integration.mjs`.
The script's session storage is in memory and its destination is fixed to port 8011.

Fixture tests verify two-owner task isolation and bounded, recoverable failure
controls. Browser sign-out, session restoration, account-switch races and live
Calendar/Docs recovery remain separate acceptance checks.

## Calendar replacement-grant correction

A regression reproduced both an old refresh rejection and an old read rejection
disconnecting a newly connected Calendar grant. Automatic disconnect now checks
the failed request's grant identity under the connection lock. Explicit user
disconnect remains unconditional. Targeted Calendar/OAuth checks passed (5 tests),
including preservation of newly imported evidence after a replacement grant.

## Session transition checks

The installed Supabase SDK clears local state even when remote logout returns
503. The old generic retry message was misleading on the resulting sign-in page.
GhostTab now distinguishes local sign-out from confirmed remote sign-out, without
claiming other sessions ended. A retained/unknown session still gets retry guidance.

Session restoration now has a ten-second UI deadline. Late restoration cannot
override sign-out or a newer identity, and unmounted subscriptions cannot update
state. API credential lookup is bound to the workspace's account: an old action
cannot obtain the newly signed-in user's token. Five focused tests cover these
transitions; all 47 frontend tests, type/lint checks and production build passed.

The disposable browser rehearsal verified reload restoration, B seeing no A
workspace, and sign-out propagation across two tabs. These checks use the actual
Supabase client against the fixture, not live Supabase accounts.

## Final isolated recovery evidence

- Browser: unsaved-draft sign-out opens confirmation; Keep editing preserves text
  and session; Discard and leave proceeds. Injected logout 503 displays the local
  sign-out warning correctly. A fictional screenshot is saved only under ignored
  `.ghosttab/screenshots/readiness-signout.png`.
- Actual SDK: rejected proactive refresh preserves a still-valid session; rejected
  refresh of expired saved-session metadata clears it. The expired metadata lives
  only in test-owned memory. Partial logout returns the safe local warning.
- Docs: transient failure preserves the saved brief; resource denial blocks its
  evidence; rejected token refresh removes the grant. Reconnect alone restores
  neither removed evidence nor its brief. Explicit reimport and fake preparation
  produce a new current snapshot, preserving unrelated manual notes.
- The SDK integration test initially assumed every refresh rejection cleared a
  session. SDK source and the failing trial showed the valid-token distinction;
  the expectation was corrected. A Docs test likewise distinguished resource
  denial from account-level grant revocation. No application change was made to
  force those incorrect expectations.

## Remaining owner-run release gates

Final local results: 47 frontend tests, TypeScript/ESLint, 142 API tests,
Ruff lint/format and production build passed. The opt-in SDK integration check
also passed. Commands had 25–90 second process deadlines; no command exceeded
its deadline. Existing bundle/Alembic warnings remain; the new test fixture also
exposes a Starlette TestClient deprecation warning. No dependency was added.

These isolated checks do not establish real-provider expiry/reconnection behavior
or final two-live-account browser isolation. Use disposable test accounts/resources
for those checks; do not revoke the working demo's grants. Existing owner-confirmed
password recovery need not be repeated. Final two-source citation capture, video,
judge access and public email delivery remain separate delivery work.
