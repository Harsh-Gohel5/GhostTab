"""Opt-in two-source Meta baseline/update trials using fictional evidence only."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from evaluate_meta import evaluate

from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions

CALENDAR = (
    "Meeting: fictional launch handoff on November 3, 2026 at noon America/Phoenix. "
    "Maya owns the launch checklist. Lee must approve the delivery plan by "
    "November 5, 2026 at 3 PM America/Phoenix. Launch approval is pending."
)
CASES = [
    (
        "source_baseline",
        CALENDAR,
        "The accessibility review owner is unassigned. The support contact is unassigned.",
        "Retain Calendar timing and checklist ownership; leave both missing owners unknown. "
        "Do not infer whole-handoff readiness from the pending approval.",
    ),
    (
        "source_updated",
        CALENDAR,
        "Nina owns the accessibility review. The support contact is unassigned.",
        "Cite the Doc for Nina's accessibility ownership and Calendar for timing/approval. "
        "Do not keep the accessibility owner unknown, assign Nina support, or claim completion.",
    ),
]


def sources(calendar_text, document):
    return [
        ("google_calendar", "Fictional launch meeting", calendar_text),
        ("google_docs", "Fictional accessibility handoff document", document),
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        raise SystemExit("No calls. Pass --live only with owner authorization.")
    settings = Settings().model_copy(update={"meta_model_id": "muse-spark-1.3"})
    if not settings.allow_model_requests or not settings.model_api_key.get_secret_value():
        raise SystemExit("Existing model access is disabled; no configuration changed.")
    engine = make_engine(settings.database_url)
    try:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        evaluate(
            settings,
            sessions(engine),
            Path(f".ghosttab/evaluations/source-changes-{stamp}.json"),
            cases=CASES,
            evidence_builder=sources,
            task_title="Fictional launch handoff",
            source_description="fictional Calendar/Docs representations; no connector reads",
        )
    finally:
        engine.dispose()
