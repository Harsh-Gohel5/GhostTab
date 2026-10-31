# Repeatable local demo

Updated October 31, 2026. Rehearse the Calendar + Google Docs workflow in the normal
signed-in local app. The owner completed the guided workflow and reported the Docs
update test done; final before/after source-citation capture remains pending.
See [current evidence and limitations](current-status.md). Gmail, Slack, Jira and
Teams remain live-unverified. No productivity or user-study result is claimed.

## Before starting

- Run the frontend, API and worker following [setup](setup.md). The worker needs
  network access to Meta. Keep ports on loopback and the cumulative app budget at $1.
- Confirm promotional credits remain active. The app budget is estimate-based and
  is not a guarantee against provider billing. Use synthetic content only.
- Sign in and separately connect Calendar and Docs for that account. An older
  local-mode Calendar grant is not transferred into a signed-in identity. Follow
  [Google source setup](google-sources.md) for Docs API enablement and callbacks.
- Confirm both services are connected and the worker is running. Refresh the
  browser if local configuration changed. Opening Today starts no inference.
- Use Chrome while embedded-browser local access remains unresolved. Do not use
  the isolated port-8010 fixture as evidence of the real-account workflow.

## Fictional scenario

In Google Calendar, manually create a future event titled **Demo: client launch**
with this description:

> Plan the client launch handoff. Maya owns the launch checklist. Lee must approve
> the delivery plan by Thursday at 3 PM, America/Phoenix. The support contact is
> unassigned. Launch approval is still pending.

Use dates within the next 14 days. Put no customer, employer or private material
in the demonstration. GhostTab has read-only Calendar access and cannot create or
edit the event for you.

Create a Google Doc titled **GhostTab launch handoff**, using only fictional
content you are permitted to send to Meta:

> Maya owns the launch checklist. Lee must approve the delivery plan by Thursday
> at 3 PM, America/Phoenix. The support contact is unassigned. Launch approval is
> still pending.

The relative Thursday is intentionally ambiguous: an unresolved date question is
appropriate. Use an explicit date instead if the final demo should avoid that
ambiguity. The unique Doc-only fact is added during the refresh test below.

## Walkthrough

1. In Today, click **Refresh upcoming meetings**, then **Choose meeting**. The
   selected event becomes a saved workspace; other event contents are not imported.
2. Inspect the Calendar source. In that same workspace, expand **Add Google Docs
   or Gmail context**, paste the test Doc link and choose **Import document**.
   Confirm two source cards and the two-source count. A document imported into
   another workspace does not join this one automatically. Gmail can remain
   disconnected; it is not needed for this two-service test.
3. Click **Prepare brief** once. Show waiting/preparing and then the saved brief,
   facts, proposed next steps and unknowns. Waiting time may be edited out of a
   recording if disclosed. Do not portray an older saved result as a new call.
4. Click a source citation. Compare the quoted passage with the claim yourself;
   exact quote validation does not prove the interpretation is correct.
5. Edit the draft. **Copy draft** copies the current editor text; nothing is sent.
   **Save draft** persists it in GhostTab. **Download brief** requests a Markdown
   file with the brief, current editor text and cited quotes. It does not save
   editor changes or send any message.
6. In the Google Doc, add **“Nina owns the accessibility review.”** In GhostTab,
   click **Check source** on the Docs card. Show **Update needed**, the updated
   source and the preserved previous brief. Detection requires this manual check;
   changing the external Doc alone does not update GhostTab automatically.
   Save or discard any draft edits first; checking Calendar and updating a brief
   are paused while draft edits are unsaved.
7. Click **Update brief** once. Confirm Nina's responsibility appears with a
   Google Docs citation whose exact quote supports it. Inspect a Calendar-backed
   timing claim too. Record both citations so the test demonstrates two sources,
   rather than just a second connected account. Review the revised draft before
   using it. **Make dates readable** is an explicit edit; then **Save draft**.
8. Return to Today. Show the workspace under **Ready to review**. **Review brief**
   opens saved content without another model call when its context is unchanged.

## Checks before recording

- [ ] Calendar and Docs are both authorized and imported into the same workspace.
- [ ] Both sources have inspectable supporting citations after the Doc-only update.
- [ ] Each prepared claim can be inspected against a stored source quote.
- [ ] Changed context marks the brief stale and a manual update creates a new brief.
- [ ] Draft editing, copy feedback and download work; no message is sent.
- [ ] Show actual model usage estimates and keep provider billing claims qualified.
- [ ] Hide keys, credentials, account billing details and unrelated private events.
- [ ] Recheck recovery/isolation/reconnect separately; this walkthrough does not
  establish all account or failure behavior.

If a provider fails, show the error/retry state. A labeled fixture replay can
explain the UI, but cannot establish that a live call succeeded. A cached result
must be identified as previously prepared.
