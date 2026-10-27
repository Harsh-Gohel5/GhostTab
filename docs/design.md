# GhostTab interface direction

Approved October 26, 2026: **light neutral, indigo and teal**.

Use a near-white page, opaque white panels, ink-colored primary text and readable
slate secondary text. Indigo identifies the main action, selected navigation and
keyboard focus. Teal supplies small contextual highlights and positive status;
status text accompanies color. Warm warning and error colors retain separate roles.

The palette is defined once as semantic tokens in `apps/web/src/styles.css`.
The Today welcome panel blends a light indigo tint into a quiet teal tint. Avoid
spreading saturated fills across every card or reducing text contrast for softness.
Use spacing, readable type and restrained surfaces to keep the experience calm.

Engagement comes from useful actions: inspect sources, review a draft, see saved
feedback and follow the task's preparation state. Hover feedback and brief entry
motion are restrained and honor reduced-motion preferences. Keyboard focus remains
visible. Small labels have a minimum size of 11px; key action labels use 12px or more.

This milestone changes presentation, not provider access. Google authorization and
live model verification remain separate steps. Meta requests stay disabled by default.

## Brief preparation feedback

The workspace shows Save context → Prepare brief → Review & edit. These steps
describe real states, without an estimated percentage or completion time. Queued
and running requests show different messages; users can leave and return to a
durable job. The workspace polls active jobs every two seconds while open.

Changed sources show an amber Update needed state and label the saved output
Previous brief. Earlier citation revisions remain available for review. The
primary action becomes Update brief. Only a job for the current source generation
can show an active preparation or failure for that revision.

Failures use plain-language recovery instructions for connection, access, budget,
output validation and attempt-limit problems. Retry is offered for recoverable
failures when preparation is enabled. When preparation is paused, notes, sources
and saved drafts remain available. Status messages use live regions, and the
three-step layout stacks on small screens.

An unchanged, prepared workspace offers Review brief, which scrolls to and focuses
the saved brief without submitting another model request. The Review & edit step
also navigates to the content (including an explicitly labeled previous brief
when stale). Reviewing remains available when AI preparation is paused. After a
source change, Update brief submits the new revision; repeated preparation of an
unchanged successful revision is deduplicated by the API.

## Today readiness

Today groups saved workspaces into Needs attention, Ready to review and All. Rows
distinguish missing sources, an unprepared source packet, changed context, active
preparation and failed jobs. The action opens the workspace; it never starts a
model call from the overview. Preparing jobs are polled every two seconds while
Today is open. Returning to Today refreshes saved task state.

Calendar rows use the exact event ID to locate an imported workspace. Unselected
events are labeled Not saved yet. Status describes saved context and explicitly
directs users to Check Calendar for newer event data. Five matching workspaces
are shown before the All workspaces link; the API currently loads at most 100.

## Take the result with you

Draft actions distinguish Save draft (persist in GhostTab), Copy draft (current
editor text to clipboard), and Download brief (current editor text plus the saved
brief and supporting quotes as Markdown). Copy and download never send a message
or start inference. Copy failures provide manual-copy instructions.

Downloads use the snapshot's cited quotes, not newer source text, and mark stale
briefs as outdated. Full source bodies are not exported. Untrusted text is escaped
or fenced so it cannot introduce embedded Markdown media or HTML. The draft fence
is longer than any backtick sequence in its contents. Download feedback states
that the download was requested; browser settings still control saving the file.
