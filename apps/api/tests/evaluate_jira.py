"""Explicit bounded Meta review/trials. Never reads environment files as evidence."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from evaluate_meta import evaluate

from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions

CASES = [
    (
        "jira_conflict",
        "Launch is approved for November 2, 2026 at 3 PM America/Phoenix.",
        (
            "Issue DEMO-1. Status: Blocked. Approval is pending; no approver assigned. "
            "Neither source has verified precedence."
        ),
        (
            "Expose approval conflict and missing approver; do not claim the issue is "
            "done or anything was sent."
        ),
    ),
    (
        "jira_revision",
        (
            "Launch target: November 2, 2026 at 3 PM America/Phoenix. Maya owns only the "
            "launch checklist."
        ),
        (
            "Issue DEMO-1 updated: Status: In progress. This replaces its earlier "
            "Blocked status. Delivery approval is still pending; approver unassigned."
        ),
        (
            "Use the revised In progress status; keep delivery approver unknown and do "
            "not transfer Maya's ownership."
        ),
    ),
]


def review_sources(first, second):
    return [
        ("manual", "Jira implementation part 1", first),
        ("manual", "Jira implementation part 2", second),
    ]


def workflow_sources(email, issue):
    return [("gmail", "Fictional launch email", email), ("jira", "Fictional Jira issue", issue)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--review", action="store_true")
    args = parser.parse_args()
    if not args.live:
        raise SystemExit("No calls made. Pass --live with owner authorization.")
    settings = Settings()
    if not settings.allow_model_requests or not settings.model_api_key.get_secret_value():
        raise SystemExit("Existing model access is disabled; no configuration changed.")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    engine = make_engine(settings.database_url)
    try:
        if args.review:
            code = Path("apps/api/src/ghosttab_api/jira_sources.py").read_text(encoding="utf-8")
            if len(code) > 24_000:
                raise SystemExit("Review evidence exceeds two bounded sources; no calls made.")
            split = len(code) // 2
            cases = [
                (
                    "jira_code_review",
                    code[:split],
                    code[split:],
                    (
                        "Review concrete correctness/authorization bugs. Cite code exactly. "
                        "Distinguish verified code facts from hypotheses; propose tests, "
                        "never claim "
                        "execution."
                    ),
                )
            ]
            evaluate(
                settings.model_copy(update={"meta_model_id": "muse-wonder-1.0"}),
                sessions(engine),
                Path(f".ghosttab/evaluations/jira-review-{stamp}.json"),
                cases=cases,
                evidence_builder=review_sources,
                task_title="Review Jira connector implementation",
                task_goal=(
                    "Find concrete bugs in this read-only Jira OAuth/import/refresh "
                    "implementation. Focus on authorization races, rotating refresh grants and "
                    "site revocation. Return actionable findings with exact code quotes; avoid "
                    "speculative issues. No tools or code execution."
                ),
                source_description="own repository source only; no credentials or user data",
            )
        else:
            evaluate(
                settings.model_copy(update={"meta_model_id": "muse-spark-1.3"}),
                sessions(engine),
                Path(f".ghosttab/evaluations/jira-trials-{stamp}.json"),
                cases=CASES,
                evidence_builder=workflow_sources,
                task_title="Fictional launch task",
                source_description="fictional email/Jira issue; not live connectors",
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
