# Account access

## Google identity sign-in

**Continue with Google** now starts Supabase's Google OAuth flow from sign-in or
sign-up. It requests `openid email profile` only, with a same-origin application
callback. It does not create Calendar, Docs, Gmail or Slack source grants and
does not reuse the Google identity token for connector reads.

Enable Google under Supabase Auth providers and configure its client ID/secret
there; a dedicated Google OAuth web client keeps identity setup distinct from the
existing Calendar integration. Register the Supabase callback shown in the provider
dashboard (normally `https://PROJECT.supabase.co/auth/v1/callback`) in Google Cloud,
and allow the GhostTab frontend URL in Supabase redirects. These are different
from GhostTab's Calendar/Docs/Gmail callback URLs. No provider configuration or
live Google consent was performed. A declined/failed callback shows a generic
retry message. The 8011 fixture supplies a simulated Google identity callback for
browser testing; it never opens Google or proves real identity verification.

Reference: [Supabase Google sign-in](https://supabase.com/docs/guides/auth/social-sign-in/auth-google).

October 29, 2026. Email sign-up, confirmation guidance/resend, sign-in, generic
recovery requests and password update are implemented through the existing
Supabase JavaScript SDK. Busy/error states and password visibility are included.
New passwords need eight characters and matching confirmation. Passwords are never
trimmed, sent to GhostTab's API, logged, or sent to Meta. The profile name is stored
as Supabase user metadata and displayed as an initial/name in the app.

The normal local app remains unchanged at port 5173: its five workspaces and
Calendar grant are not migrated into a new account. Local mode is device-only
development access, not a fake email account. Supabase mode is enabled only with
the existing `GHOSTTAB_AUTH_MODE=supabase`, HTTPS `GHOSTTAB_SUPABASE_URL`, and
`GHOSTTAB_SUPABASE_PUBLISHABLE_KEY`. Do not use a service-role key in the browser.

Configure the provider's email/password sign-up and confirmation policy and
register the frontend site URL/redirects. For local verification these are
`http://127.0.0.1:5173/` and `http://127.0.0.1:5173/?auth=recovery`; future hosted
operation needs the corresponding approved HTTPS URLs. Recovery uses the SDK's
PASSWORD_RECOVERY event and authenticated updateUser operation. The SDK handles
session/callback tokens; query parameters alone do not establish a session.

The API still validates JWT signatures, issuer, audience, expiry and authenticated
role, and scopes every workspace to the verified subject. It trusts neither the
profile name nor browser session claims for ownership. Account changes/sign-out
cancel and remove owner-scoped cached queries. Unsaved-draft navigation protection
still applies to sign-out. Session restoration cannot overwrite a newer auth event.

## Verification boundary

Unit tests cover exact password handling, matching/short-password rejection,
fixed callback construction, confirmation-without-session handling, generic error
and recovery messaging, and update submission. Existing API tests exercise signed
JWT acceptance/rejection and owner isolation. The isolated browser rehearsal passed
sign-up confirmation, sign-in, reload restoration, sign-out, recovery request and
recovery callback/password update.

**Live Supabase project configuration, real email delivery, actual confirmation
links and hosted account isolation remain unverified.** No real account was created
and no external email was sent during this milestone. Complete those checks before
calling hosted authentication ready for users.

For a disposable rehearsal, build the web app and run
`.venv/Scripts/python.exe apps/api/tests/auth_browser_fixture.py`, then open
http://127.0.0.1:8011/. The banner explicitly identifies simulated authentication.
Use `demo@example.test` / `demo-password` only in this fixture. The fixture has its
own temporary database and local token verifier, which is never installed in the
normal app. The test-only `/synthetic-recovery` page supplies a simulated recovery
link; it sends no email and does not verify real delivery or production JWTs.

Reference: [Supabase sign-up](https://supabase.com/docs/reference/javascript/auth-signup),
[password recovery](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail).
