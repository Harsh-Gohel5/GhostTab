from fastapi import HTTPException
from sqlalchemy import func, select, update

from ghosttab_api.models import Evidence, EvidenceVersion, Job, Snapshot, Task, new_id


def owned_task(session, task_id, owner_id, *, lock=False):
    condition = (Task.id == task_id, Task.owner_id == owner_id)
    if lock:
        # Serializes evidence edits, job admission and publication on both databases.
        session.execute(update(Task).where(*condition).values(generation=Task.generation))
    task = session.scalar(select(Task).where(*condition).execution_options(populate_existing=True))
    if not task:
        raise HTTPException(404, "Workspace not found")
    return task


def evidence_packet(session, task_id):
    rows = session.execute(
        select(Evidence, EvidenceVersion)
        .join(EvidenceVersion, Evidence.version_id == EvidenceVersion.id)
        .where(Evidence.task_id == task_id, Evidence.removed.is_(False))
        .order_by(Evidence.id)
    ).all()
    return [
        {
            "id": item.id,
            "version_id": version.id,
            "title": version.title,
            "content": version.content,
            "url": version.url,
            "origin": item.origin,
            "observed_at": version.created_at,
        }
        for item, version in rows
    ]


def put_evidence(session, task, data, *, item=None, origin="manual"):
    if item is None:
        if len(evidence_packet(session, task.id)) >= 8:
            raise HTTPException(422, "Use at most eight focused sources per workspace")
        item = Evidence(id=new_id(), task_id=task.id, version_id=new_id(), origin=origin)
        session.add(item)
        session.flush()
    else:
        previous = session.get(EvidenceVersion, item.version_id)
        if (previous.title, previous.content, previous.url) == (data.title, data.content, data.url):
            return item
        item.version_id = new_id()
    session.add(EvidenceVersion(id=item.version_id, evidence_id=item.id, **data.model_dump()))
    task.generation += 1
    session.flush()
    return item


def visible_snapshot(session, task_id):
    snapshot = session.scalar(
        select(Snapshot)
        .where(Snapshot.task_id == task_id)
        .order_by(Snapshot.generation.desc())
        .limit(1)
    )
    if snapshot:
        allowed = {
            x.id
            for x in session.scalars(
                select(Evidence).where(Evidence.task_id == task_id, Evidence.removed.is_(False))
            )
        }
        if not all(x["id"] in allowed for x in snapshot.manifest):
            return None
    return snapshot


def task_view(session, task):
    job = session.scalar(
        select(Job).where(Job.task_id == task.id).order_by(Job.generation.desc()).limit(1)
    )
    snapshot = visible_snapshot(session, task.id)
    return {
        "id": task.id,
        "title": task.title,
        "goal": task.goal,
        "generation": task.generation,
        "created_at": task.created_at,
        "from_calendar": bool(task.calendar_event_id),
        "calendar_event_id": task.calendar_event_id,
        "source_count": session.scalar(
            select(func.count())
            .select_from(Evidence)
            .where(Evidence.task_id == task.id, Evidence.removed.is_(False))
        ),
        "freshness": "unprepared"
        if not snapshot
        else ("current" if snapshot.generation == task.generation else "stale"),
        "job": job_view(job) if job else None,
    }


def job_view(job):
    return {
        "id": job.id,
        "task_id": job.task_id,
        "generation": job.generation,
        "status": job.status,
        "attempts": job.attempts,
        "error_code": job.error_code,
        "created_at": job.created_at,
    }
