"""Local worker presence, not a provider health check or billing guarantee."""

import time
from contextlib import contextmanager
from threading import Event, Thread

from sqlalchemy import delete, select

from ghosttab_api.models import Budget, WorkerHeartbeat, new_id

HEARTBEAT_INTERVAL = 10
HEARTBEAT_TTL = 45


def touch_worker(factory, worker_id):
    now = time.time()
    with factory.begin() as session:
        session.execute(delete(WorkerHeartbeat).where(WorkerHeartbeat.seen_at < now - 86400))
        row = session.get(WorkerHeartbeat, worker_id)
        if row:
            row.seen_at = now
        else:
            session.add(WorkerHeartbeat(id=worker_id, seen_at=now))


@contextmanager
def worker_presence(factory):
    worker_id = new_id()
    touch_worker(factory, worker_id)
    stop = Event()

    def heartbeat():
        while not stop.wait(HEARTBEAT_INTERVAL):
            try:
                touch_worker(factory, worker_id)
            except Exception:
                # A failed database heartbeat expires naturally; never report false readiness.
                import logging

                logging.warning("Preparation service heartbeat failed")

    thread = Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        yield worker_id
    finally:
        stop.set()
        thread.join(timeout=5)
        with factory.begin() as session:
            session.execute(delete(WorkerHeartbeat).where(WorkerHeartbeat.id == worker_id))


def preparation_status(session, settings):
    now = time.time()
    present = (
        session.scalar(
            select(WorkerHeartbeat.id)
            .where(
                WorkerHeartbeat.seen_at > now - HEARTBEAT_TTL,
                WorkerHeartbeat.seen_at <= now + 5,
            )
            .limit(1)
        )
        is not None
    )
    budget = session.get(Budget, 1)
    if not settings.allow_model_requests:
        state = "disabled"
    elif not settings.model_api_key.get_secret_value():
        state = "unconfigured"
    elif not budget or budget.charged_microusd >= int(settings.model_budget_usd * 1_000_000):
        state = "budget_exhausted"
    elif not present:
        state = "offline"
    else:
        state = "ready"
    return {"state": state, "worker_available": present}
