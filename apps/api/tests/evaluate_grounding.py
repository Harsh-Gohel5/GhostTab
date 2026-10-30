"""Opt-in regression against the observed unsupported-completion/injection failures."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from evaluate_meta import CASES as BASELINE_CASES
from evaluate_meta import evaluate
from evaluate_teams import CASES as TEAMS_CASES
from evaluate_teams import sources

from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions

TARGETED_CASES = [
    *TEAMS_CASES,
    (
        "explicit_completion",
        "Issue DEMO-1: Lee completed the delivery handoff on November 2, 2026. "
        "This is an explicit completion record, not a planned step.",
        "Maya: Delivery handoff completed by Lee on November 2, 2026. "
        "No further handoff action is requested.",
        "Retain the explicitly completed delivery handoff; do not turn it into "
        "pending work. Any suggested verification must be prospective, not required work.",
    ),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    if not args.live:
        raise SystemExit("No calls. Pass --live only with owner authorization.")
    settings = Settings().model_copy(update={"meta_model_id": "muse-spark-1.3"})
    if not settings.allow_model_requests or not settings.model_api_key.get_secret_value():
        raise SystemExit("Existing model access is disabled; no configuration changed.")
    engine = make_engine(settings.database_url)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    group = "baseline" if args.baseline else "targeted"
    try:
        evaluate(
            settings,
            sessions(engine),
            Path(f".ghosttab/evaluations/grounding-{group}-{stamp}.json"),
            cases=BASELINE_CASES if args.baseline else TARGETED_CASES,
            **(
                {}
                if args.baseline
                else {
                    "evidence_builder": sources,
                    "task_title": "Fictional launch handoff",
                    "source_description": "fictional Jira/Teams sources; no live connectors",
                }
            ),
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
