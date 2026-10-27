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
