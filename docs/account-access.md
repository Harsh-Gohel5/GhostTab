# Account access

November 1 readiness follow-up: session restoration has a ten-second UI deadline,
request credentials are bound to the active workspace account, and partial logout
distinguishes local sign-out from remote confirmation. Disposable two-account,
cross-tab, unsaved-draft and SDK checks are recorded in
[release readiness](release-readiness.md). Final live-account isolation remains
pending. The ignored November 1 release summary records owner confirmation of the
recovery return-to-sign-in behavior; older pending statements below are historical.

November 1 recovery refinement: after a successful password update, GhostTab ends
the recovery browser's Supabase session (`scope: local`) and returns to email
sign-in with a success message. There is no direct workspace continuation. A
failed sign-out offers a retry without resubmitting the password update. Other
browser/device sessions are not globally revoked by this action. The owner
confirmed the earlier live recovery/update flow; this new return-to-sign-in
behavior still needs owner verification after the fix.

## Google sign-in availability and setup

The account page checks `/api/auth/providers` against Supabase's public Auth
settings before enabling Google sign-in. Disabled, malformed, unavailable or timed
out responses keep email authentication usable and show a retry action. The read
is bounded to three seconds, does not follow redirects and returns only Google
availability, never the provider payload. Rechecking picks up provider changes
without restarting GhostTab. This check does not prove a completed OAuth flow.

If Supabase returns `Unsupported provider: provider is not enabled`, enable Google
in **Authentication → Sign In / Providers → Google**. A Supabase publishable key
does not enable Google's provider; it requires Google's OAuth client credentials.

1. In the existing Google Cloud project, open **APIs & Services → Credentials**.
2. Open a **Web application** OAuth client. A dedicated sign-in client is preferred;
   reusing the Calendar web client is supported if all Calendar callbacks remain.
3. Add the exact Supabase callback shown in its Google provider settings to the
   Google client's **Authorized redirect URIs**. Its form is
   `https://PROJECT_REF.supabase.co/auth/v1/callback`. Preserve existing callbacks.
4. Save the Google client ID and client secret in Supabase's Google provider form,
   enable the provider, and save. Do not use the Supabase publishable key here.
5. Allow GhostTab's frontend/recovery URLs in Supabase URL Configuration. Return to
   GhostTab and choose **Check Google sign-in again**, then complete Google consent.

Real public configuration has been connected locally; email signup/confirmation,
sign-in and completed Google sign-in were reported working by the owner on
October 30. After provider setup, the real settings check confirmed Google enabled
and the authorization endpoint redirected to Google with the expected callback.
On October 31, owner screenshots showed a signed-in Calendar import and prepared
workspace, and the owner reported the Docs workflow complete in that account.
Recovery/password update and final live account-isolation rehearsal remain pending.
This does not replace the automated JWT/ownership tests. Provider credentials
remain outside Git. See [current status](current-status.md).

Supabase's built-in SMTP is restricted to project-team email addresses and currently
two messages per hour. Public signup/recovery requires suitable custom SMTP setup;
do not present default email delivery as a production-ready service.
See [SMTP restrictions](https://supabase.com/docs/guides/auth/auth-smtp).

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
from GhostTab's Calendar/Docs/Gmail callback URLs. The owner completed local Google
provider configuration and reported successful sign-in. A declined/failed callback shows a generic
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

The isolated rehearsal above did not create a real account or send email. Later,
the owner configured a real Supabase project and confirmed email signup,
confirmation and sign-in, then Google sign-in and signed-in workspace use.
Recovery/password update, general-public email delivery and final live account
isolation remain unverified. This is not a production-authentication certification.

For a disposable rehearsal, build the web app and run
`.venv/Scripts/python.exe apps/api/tests/auth_browser_fixture.py`, then open
http://127.0.0.1:8011/. The banner explicitly identifies simulated authentication.
Use `demo@example.test` / `demo-password` only in this fixture. The fixture has its
own temporary database and local token verifier, which is never installed in the
normal app. The test-only `/synthetic-recovery` page supplies a simulated recovery
link; it sends no email and does not verify real delivery or production JWTs.

Reference: [Supabase sign-up](https://supabase.com/docs/reference/javascript/auth-signup),
[password recovery](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail).
