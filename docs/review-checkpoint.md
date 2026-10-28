# Proposed PR checkpoint

Prepared October 27, 2026. This is a local review artifact, not an opened PR.

**Proposed title:** Make brief review safer and meeting dates readable

**Base:** protected `main`. **Working branch:** `codex/draft-safety`.
The branch carries the existing copy/export commit from closed, unmerged PR #6.
Leave #6 closed; a new PR would include that existing functionality and the
review improvements below. Main and the original feature branch are unchanged.

## Proposed description

Unsaved draft edits could disappear during navigation or brief replacement, and
two tabs could overwrite each other's saved text. Briefs and Calendar sources
also exposed ISO timestamps that were difficult to read.

Add explicit navigation/discard confirmation, preserve unsaved text when newer
briefs arrive, and require comparison before saving across a conflict. The API
checks the loaded draft under the task lock, preserving exact whitespace and
allowing idempotent retries. Typing during a save remains unsaved until saved again.

Format meeting dates with month names, AM/PM times and explicit source offsets.
Group same-day source schedules, preserve all-day dates, and retain original source
text and exact citation quotes. Existing drafts offer an explicit formatting edit.
Carry forward copy-current-draft and cited Markdown export from the existing
unmerged feature. Neither action sends a message or starts inference.

Update preparation instructions after the fictional live rehearsal exposed an
incorrect relative meeting date and ambiguous checklist ownership. Record the
findings without claiming that prompt changes guarantee semantic correctness.
Add an isolated browser fixture and update setup/design/architecture explanations.

### Validation

- `npm run check`: TypeScript, ESLint, 17 frontend tests, Ruff and 28 API tests.
- `npm run build`: production bundle succeeds; existing size warning remains.
- `git diff --check`: passes.
- Browser: save/reopen, canceled navigation, Escape/discard, two-tab conflicts,
  new-brief recovery, copy/download, readable live Calendar dates, and 320px dialog.
- Live fictional Calendar import/preparation and exact deadline quote reviewed;
  schedule change marked the previous snapshot stale and retained its old quote.
  Subsequent UI review showed the regenerated brief with the changed schedule.
- No schema migration, provider-scope expansion, billing change or deployment.

### Limits and follow-ups

PostgreSQL checks must pass in the new PR's required CI before merging. No fresh
PostgreSQL run is claimed locally. Unsaved edits have no browser-crash recovery.
Local Windows reload-wrapper behavior requires the documented manual API restart.
Claim-support evaluation remains a small fictional example, not a user study.
The planned change to the description's approval deadline from noon to 3 PM has
not been verified; the observed source change was to the meeting schedule.

## Publication boundary

Include application changes, regression tests, browser fixture and relevant docs.
Keep `.env`, `.ghosttab`, downloaded files, screenshots with account data, tokens,
source grants and private application records out of Git. Preserve the original
untracked `CODEX_HANDOFF.md` locally; it is not part of this proposed PR.

The owner approved committing, pushing and opening this PR, and requested prompt
closure when everything is correct. Proceed with squash merging after final diff
review, passing required CI and resolved conversations. Preserve main protection.
