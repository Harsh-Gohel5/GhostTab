# Contributing

Use a short descriptive branch for each feature or fix. Keep changes focused and
include a clear account of the behavior and how it was verified.

## Protected main workflow

`main` is protected by the active **Protect main — pull requests and CI** ruleset.
It requires a pull request, an up-to-date branch, successful `web` and `api` checks
from GitHub Actions, resolved review conversations, and squash merging. Force
pushes and branch deletion are blocked. The bypass list is empty, including for
the owner. Do not disable protection to get a change through.

Start a short feature/fix branch from current `origin/main`; keep one focused change
per PR. Inspect the final diff and test results before merging through GitHub.
After merging, fast-forward local main with `git pull --ff-only`. For a regression,
use a revert on a new branch and another PR rather than rewriting main's history.

The project currently has one human contributor, so independent approval is not a
required gate: GitHub does not allow authors to approve their own PR. Review the
diff before merging; once another reviewer joins, require their approval. Automated
checks are required now and do not replace code review.

1. Follow the setup in README.md.
2. Run `npm run check` and `npm run build` before opening a pull request.
3. Add meaningful regression tests when implementing behavior or fixing a bug.
4. Keep credentials and real private source data out of commits and fixtures.
5. Update the docs when setup, configuration or product behavior changes.

Use synthetic examples until a source has been explicitly authorized for use.
Clearly label mocks and planned capabilities. Do not claim model integration or
successful reproduction from placeholder data.
