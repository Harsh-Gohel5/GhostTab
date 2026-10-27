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
