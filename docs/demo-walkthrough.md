# Repeatable local demo

Updated October 27, 2026. Demonstrate the working Calendar-and-notes slice honestly.
Calendar is the only live source connector. Notes are manually added; email, Slack,
document retrieval and hosted judge access are not implemented. No measured time
savings or user-study result is claimed.

## Before starting

- Run the frontend, API and worker following [setup](setup.md). The worker needs
  network access to Meta. Keep ports on loopback and the cumulative app budget at $1.
- Confirm promotional credits remain active. The app budget is estimate-based and
  is not a guarantee against provider billing. Use synthetic content only.
- Confirm Calendar is connected and the worker is running. Refresh the browser if
  local configuration changed. Opening Today itself does not start inference.

## Fictional scenario

In Google Calendar, manually create a future event titled **Demo: client launch**
with this description:

> Plan the client launch handoff. Maya owns the checklist. Lee must approve the
> delivery plan by Thursday at noon, America/Phoenix. The support contact has not
> been assigned.

Use dates within the next 14 days. Put no customer, employer or private material
in the demonstration. GhostTab has read-only Calendar access and cannot create or
edit the event for you.

## Walkthrough

1. In Today, click **Refresh upcoming meetings**, then **Choose meeting**. The
   selected event becomes a saved workspace; other event contents are not imported.
2. Inspect the imported source. Use **Add notes** for a fictional extra detail:
   “For this demo, include the delivery checklist in the handoff agenda.” Explain
   that these are manually supplied notes, not an email connector.
3. Click **Prepare brief** once. Show waiting/preparing and then the saved brief,
   facts, proposed next steps and unknowns. Waiting time may be edited out of a
   recording if disclosed. Do not portray an older saved result as a new call.
4. Click a source citation. Compare the quoted passage with the claim yourself;
   exact quote validation does not prove the interpretation is correct.
5. Edit the draft. **Copy draft** copies the current editor text; nothing is sent.
   **Save draft** persists it in GhostTab. **Download brief** requests a Markdown
   file with the brief, current editor text and cited quotes. It does not save
   editor changes or send any message.
6. In Google Calendar, change the description's deadline from noon to 3 PM. In
   GhostTab, click **Check Calendar**. Show **Update needed** and the previous
   brief's original quote. Updates are detected by this manual check.
7. Click **Update brief** once. Confirm the new deadline is reflected and the
   source quote matches. Review any revised draft before using it.
8. Return to Today. Show the workspace under **Ready to review**. **Review brief**
   opens saved content without another model call when its context is unchanged.

## Checks before recording

- [ ] The Calendar event, manual note and their roles are correctly labeled.
- [ ] Each prepared claim can be inspected against a stored source quote.
- [ ] Changed context marks the brief stale and a manual update creates a new brief.
- [ ] Draft editing, copy feedback and download work; no message is sent.
- [ ] Show actual model usage estimates and keep provider billing claims qualified.
- [ ] Hide keys, credentials, account billing details and unrelated private events.

If a provider fails, show the error/retry state. A labeled fixture replay can
explain the UI, but cannot establish that a live call succeeded. A cached result
must be identified as previously prepared.
