# Run the first working slice

## Cost boundary

The owner requires no charges during setup and development. Keep everything local.
No hosted database, hosting subscription, credit card, paid service, GPU, or cloud
deployment is needed. npm and pip install free dependencies; funding messages are
optional donation notices. No purchases are authorized.

Meta requests are **off by default**, including when a key is present. Automated
tests use synthetic data and mocked providers. No real Google consent or Meta
inference has been verified as part of implementing this slice.

Google documents standard Calendar API use at no additional cost within its daily
threshold. GhostTab requests up to 25 upcoming primary-calendar events per manual
refresh, with no scheduled polling. Do not link billing or accept an upgrade prompt.
See [Calendar usage/pricing](https://developers.google.com/workspace/calendar/api/guides/quota).
The public repository uses standard Ubuntu CI runners, documented as free by
[GitHub](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## 1. Run locally without credentials

Install dependencies following README.md. Copy `.env.example` to `.env` only if
that file does not already exist. Keep local identity and the default SQLite URL.
From the repository root:

```powershell
npm.cmd run db:migrate
npm.cmd run dev:api
```

In a second terminal:

```powershell
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Use **New workspace**, enter a task/meeting and goal,
then **Add notes**. Data persists in the ignored `.ghosttab/ghosttab.db` file.
Creating a workspace does not call a model. **Prepare with Meta** remains disabled.

Use numeric loopback consistently. Local identity checks loopback clients, host,
origin, and a custom header. It is single-user development access, not hosted
authentication. Do not expose development ports using a public tunnel.
SQLite and PostgreSQL are alternatives, not synchronized copies; changing the URL
does not transfer existing tasks. Run migrations against the chosen database.

## 2. Configure Google Calendar

This configures **the GhostTab application**. A Calendar plugin connected to
ChatGPT would be a separate integration and would not configure this app.

1. Open [Google Cloud Console](https://console.cloud.google.com/), and select/create
   a dedicated project without enabling paid services or linking billing.
2. Enable **Google Calendar API**. If a payment/upgrade is required, stop there;
   manually added notes remain usable.
3. Configure Google Auth Platform branding, audience, and data access. For an
   external Testing app, add your own Google account as a test user.
4. Request only `https://www.googleapis.com/auth/calendar.events.readonly`.
   This scope can read events on calendars you can access; GhostTab currently
   reads only the primary calendar. No event-write permission is requested.
5. Create an OAuth **Web application** client. Register this exact redirect:
   `http://127.0.0.1:8000/api/connections/google/callback`.
6. Put its client ID and secret in the local `.env`:

```dotenv
GHOSTTAB_GOOGLE_CLIENT_ID=your-client-id
GHOSTTAB_GOOGLE_CLIENT_SECRET=your-client-secret
GHOSTTAB_GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/api/connections/google/callback
```

7. Generate the token encryption key **locally**, then paste it into that file:

```powershell
.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```dotenv
GHOSTTAB_TOKEN_ENCRYPTION_KEY=paste-the-generated-key-here
```

Keep that output private. Changing the key makes existing stored tokens unreadable.
Never paste credentials into chat, commits, screenshots, issues, or frontend variables.

8. Restart the API. Open **Connections → Connect Calendar**, and complete Google's
   consent yourself in that browser. The flow uses a single-use, ten-minute state,
   browser-binding cookie and PKCE. Tokens are encrypted on the server.
9. In **Today**, choose a meeting. Inspect its imported description, location and
   time. Attachments, linked document contents and attendee email lists are not fetched.
10. Change the event in Google Calendar, then use **Check Calendar** in its workspace.
    A changed normalized source creates a revision and makes the brief stale. This
    is a manual check, not real-time synchronization.

Disconnect deletes stored tokens, invalidates pending authorization and blocks
snapshots that use Calendar evidence. It does not purge historic source versions
from storage or revoke the upstream Google grant. Use Google's third-party access
page to remove the upstream grant too. A retention/purge feature is still future work.
External Testing refresh tokens can expire after seven days; reconnect before the demo.
See [Google's web authorization guide](https://developers.google.com/identity/protocols/oauth2/web-server)
and [Calendar scope guidance](https://developers.google.com/workspace/calendar/api/auth).

## 3. Enable Meta after verifying credit-only use

First check the approved $150 credit's balance, expiry, eligible model and overage
behavior in the [Meta dashboard](https://dev.meta.ai/). Set provider-side spending
controls where available. Application estimates cannot guarantee provider billing;
if credit-only use or stopping overages cannot be confirmed, leave requests disabled.
Do not add a paid fallback provider or payment method.

Once verified and ready for a real synthetic smoke test, configure locally:

```dotenv
MODEL_API_KEY=your-meta-project-key
META_MODEL_ID=muse-spark-1.3
GHOSTTAB_ALLOW_MODEL_REQUESTS=true
GHOSTTAB_MODEL_BUDGET_USD=1
```

Use a $1 application ceiling initially. It is cumulative against the database ledger,
not a daily allowance or substitute for provider billing controls. Reconcile usage
with the dashboard. Restart the API and start the separate worker:

```powershell
npm.cmd run dev:worker
```

Select a synthetic workspace and **Prepare with Meta**. This submits model input
and may consume credit. The worker validates structure and exact citation spans,
then saves the brief and editable unsent draft. Inspect claims yourself: matching
quotes do not prove factual support. There are at most three submissions per source
generation, including crash recovery and bounded transient retries. A timeout keeps
the full cost reservation because billing may have occurred. No raw chain of thought
is stored. See [model-budget.md](model-budget.md).

## 4. Optional hosted identity and PostgreSQL later

No hosted account or resource has been created. Local development needs neither.
Any deployment requires a separate check of free-plan limits and billing settings.

The API supports Supabase JWT verification with ES256/RS256 keys, and the UI supports
existing-user email/password sign-in. Configure `GHOSTTAB_AUTH_MODE=supabase`,
`GHOSTTAB_SUPABASE_URL`, and `GHOSTTAB_SUPABASE_PUBLISHABLE_KEY`. Use asymmetric signing
keys; legacy HS256 is unsupported. Sign-up and password recovery are not built yet.

Set `GHOSTTAB_DATABASE_URL=postgresql+psycopg://…` using a trusted server role, then
run migrations. They enable RLS and remove public/browser-role grants on application
tables. All browser data access goes through FastAPI owner checks. A JWT does not
configure PostgreSQL identity automatically. Prefer a dedicated database and scope
server-role permissions before deployment. Production settings require PostgreSQL,
Supabase, and an HTTPS frontend. Hosting and production asset serving remain future work.
