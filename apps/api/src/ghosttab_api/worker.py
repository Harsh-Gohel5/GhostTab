import hashlib
import json
import logging
import threading
import time

from pydantic import ValidationError
from sqlalchemy import and_, or_, select, update

from ghosttab_api.config import Settings
from ghosttab_api.database import make_engine, sessions
from ghosttab_api.meta import (
    PROMPT_VERSION,
    MetaClient,
    ModelFailure,
    actual_cost,
    request_body,
    reservation,
    validate_brief,
)
from ghosttab_api.models import Budget, Job, ModelRun, Snapshot, Task, new_id
from ghosttab_api.readiness import worker_presence
from ghosttab_api.workspaces import evidence_packet

LEASE_SECONDS = 180


def claim_job(factory):
    now = time.time()
    with factory.begin() as session:
        session.execute(
            update(Job)
            .where(Job.status == "running", Job.lease_until < now, Job.attempts >= 3)
            .values(status="failed", error_code="attempts_exhausted")
        )
        eligible = and_(
            Job.attempts < 3,
            or_(
                and_(Job.status == "queued", Job.available_at <= now),
                and_(Job.status == "running", Job.lease_until < now),
            ),
        )
        job_id = session.scalar(
            select(Job.id)
            .where(eligible)
            .order_by(Job.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not job_id:
            return None
        token = new_id()
        changed = session.execute(
            update(Job)
            .where(Job.id == job_id, eligible)
            .values(
                status="running",
                attempts=Job.attempts + 1,
                lease_token=token,
                lease_until=now + LEASE_SECONDS,
                error_code=None,
            )
        ).rowcount
        return (job_id, token) if changed else None


def run_once(factory, settings, client=None):
    claimed = claim_job(factory)
    if not claimed:
        return False
    job_id, token = claimed
    stop = threading.Event()

    def heartbeat():
        while not stop.wait(30):
            try:
                with factory.begin() as session:
                    session.execute(
                        update(Job)
                        .where(Job.id == job_id, Job.lease_token == token, Job.status == "running")
                        .values(lease_until=time.time() + LEASE_SECONDS)
                    )
            except Exception:
                logging.warning("Worker heartbeat failed; publication remains lease-fenced")

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    run_id = None
    try:
        if not settings.allow_model_requests:
            raise ModelFailure("model_requests_disabled")
        with factory.begin() as session:
            job = session.get(Job, job_id)
            task = session.get(Task, job.task_id)
            generation, task_id = job.generation, task.id
            if task.generation != generation:
                job.status = "superseded"
                return True
            packet = evidence_packet(session, task.id)
            if not packet:
                raise ModelFailure("evidence_required")
            body = request_body(task.title, task.goal, packet, settings.meta_model_id)
            reserved = reservation(body)
            admitted = session.execute(
                update(Budget)
                .where(
                    Budget.id == 1,
                    Budget.charged_microusd + reserved
                    <= int(settings.model_budget_usd * 1_000_000),
                )
                .values(charged_microusd=Budget.charged_microusd + reserved)
            ).rowcount
            if not admitted:
                raise ModelFailure("budget_exhausted")
            run_id = new_id()
            session.add(
                ModelRun(
                    id=run_id, job_id=job_id, model=settings.meta_model_id, cost_microusd=reserved
                )
            )

        result = (client or MetaClient(settings)).complete(body)
        # Record usage even if subsequent citation/schema validation fails.
        with factory.begin() as session:
            run = session.get(ModelRun, run_id)
            cost = actual_cost(result.usage, settings.meta_model_id)
            if cost is not None:
                session.execute(
                    update(Budget)
                    .where(Budget.id == 1)
                    .values(charged_microusd=Budget.charged_microusd + cost - run.cost_microusd)
                )
                run.cost_microusd = cost
            run.usage = {
                "provider_usage": result.usage,
                "request_id": result.request_id,
                "prompt_version": PROMPT_VERSION,
            }
            run.status = "received"
        brief = validate_brief(result.content, packet)
        manifest = [{"id": x["id"], "version_id": x["version_id"]} for x in packet]
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "body": body,
                    "manifest": manifest,
                    "prompt": PROMPT_VERSION,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        with factory.begin() as session:
            # Same task lock order as edits. Fence old workers and changed input.
            current = session.execute(
                update(Task)
                .where(Task.id == task_id, Task.generation == generation)
                .values(generation=Task.generation)
            ).rowcount
            job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
            if job.lease_token != token or job.status != "running" or job.lease_until < time.time():
                return True
            if not current:
                job.status = "superseded"
            else:
                session.add(
                    Snapshot(
                        job_id=job_id,
                        task_id=task_id,
                        generation=generation,
                        brief=brief.model_dump(),
                        manifest=manifest,
                        fingerprint=fingerprint,
                        draft=brief.draft,
                    )
                )
                job.status = "succeeded"
            session.get(ModelRun, run_id).status = "validated"
    except Exception as exc:
        code = (
            exc.code
            if isinstance(exc, ModelFailure)
            else (
                "invalid_model_output" if isinstance(exc, ValidationError) else "preparation_failed"
            )
        )
        with factory.begin() as session:
            job = session.get(Job, job_id)
            if job.lease_token == token and job.status == "running":
                retry = isinstance(exc, ModelFailure) and exc.retryable and job.attempts < 3
                job.status = "queued" if retry else "failed"
                job.available_at = time.time() + 30 * job.attempts
                job.error_code = code
            if run_id and (run := session.get(ModelRun, run_id)):
                run.status = code  # Unknown billing retains the full reservation.
    finally:
        stop.set()
        thread.join(timeout=2)
    return True


def main():
    settings = Settings()
    if not settings.allow_model_requests or not settings.model_api_key.get_secret_value():
        raise SystemExit(
            "Meta requests are disabled. See docs/setup.md before enabling the worker."
        )
    factory = sessions(make_engine(settings.database_url))
    logging.basicConfig(level=logging.INFO)
    logging.info("Preparation worker ready (no source content is logged)")
    try:
        with worker_presence(factory):
            while True:
                if not run_once(factory, settings):
                    time.sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
