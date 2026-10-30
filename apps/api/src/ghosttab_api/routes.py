import getpass
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select

from ghosttab_api import calendar
from ghosttab_api.auth import Principal, current_user
from ghosttab_api.contracts import DraftInput, EventInput, EvidenceInput, LifecycleInput, TaskInput
from ghosttab_api.models import Budget, Connection, Evidence, EvidenceVersion, Job, Task
from ghosttab_api.readiness import preparation_status
from ghosttab_api.workspaces import (
    evidence_packet,
    job_view,
    owned_task,
    put_evidence,
    task_view,
    visible_snapshot,
)

router = APIRouter(prefix="/api")
User = Annotated[Principal, Depends(current_user)]


@router.get("/config")
def config(request: Request):
    settings = request.app.state.settings
    return {
        "auth_mode": settings.auth_mode,
        "supabase_url": settings.supabase_url,
        "supabase_publishable_key": settings.supabase_publishable_key,
        "model_configured": bool(settings.model_api_key.get_secret_value())
        and settings.allow_model_requests,
        "calendar_configured": settings.google_ready,
        "synthetic_demo": settings.synthetic_demo,
        "display_name": getpass.getuser()
        if settings.auth_mode == "local" and not settings.synthetic_demo
        else "",
    }


@router.get("/connections")
def connections(request: Request, user: User):
    with request.app.state.sessions() as session:
        connection = session.get(Connection, user.id)
        budget = session.get(Budget, 1)
        return {
            "google_calendar": "connected" if connection else "not_connected",
            "estimated_usage_usd": (budget.charged_microusd / 1_000_000) if budget else 0,
            "budget_usd": request.app.state.settings.model_budget_usd,
        }


@router.get("/preparation/status")
def preparation_readiness(request: Request, user: User):
    with request.app.state.sessions() as session:
        return preparation_status(session, request.app.state.settings)


@router.post("/connections/google/start")
def connect(request: Request, user: User):
    settings = request.app.state.settings
    url, digest = calendar.begin_connection(request.app.state.sessions, settings, user.id)
    response = JSONResponse({"url": url})
    response.set_cookie(
        "ghosttab_oauth",
        digest,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=600,
        path="/api/connections/google/callback",
    )
    return response


@router.get("/connections/google/callback")
def callback(
    request: Request,
    state: Annotated[str, Query(max_length=200)] = "",
    code: Annotated[str, Query(max_length=4096)] = "",
    error: Annotated[str, Query(max_length=200)] = "",
):
    settings = request.app.state.settings
    outcome = "connected"
    try:
        calendar.finish_connection(
            request.app.state.sessions,
            settings,
            state,
            request.cookies.get("ghosttab_oauth"),
            code,
            error,
        )
    except HTTPException:
        outcome = "connection_failed"
    response = RedirectResponse(settings.frontend_url + "?calendar=" + outcome, status_code=303)
    response.delete_cookie("ghosttab_oauth", path="/api/connections/google/callback")
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.delete("/connections/google", status_code=204)
def disconnect(request: Request, user: User):
    calendar.disconnect(request.app.state.sessions, user.id)


@router.get("/calendar/events")
def events(request: Request, user: User):
    data, _ = calendar.calendar_request(
        request.app.state.sessions, request.app.state.settings, user.id
    )
    return {
        "events": [
            {
                "id": event["id"],
                "title": event.get("summary") or "Untitled meeting",
                "start": event.get("start", {}),
                "end": event.get("end", {}),
            }
            for event in data.get("items", [])
            if event.get("status") != "cancelled"
        ],
        "has_more": bool(data.get("nextPageToken")),
    }


@router.post("/tasks/from-calendar", status_code=201)
def import_event(body: EventInput, request: Request, user: User):
    data, grant = calendar.calendar_request(
        request.app.state.sessions, request.app.state.settings, user.id, body.event_id
    )
    if data.get("status") == "cancelled":
        raise HTTPException(409, "This meeting is cancelled or no longer available")
    source = calendar.event_evidence(data)
    with request.app.state.sessions.begin() as session:
        calendar.check_grant(session, user.id, grant, lock=True)
        task = session.scalar(
            select(Task).where(Task.owner_id == user.id, Task.calendar_event_id == body.event_id)
        )
        if not task:
            task = Task(
                owner_id=user.id,
                title=source.title,
                calendar_event_id=body.event_id,
                goal="Prepare for this meeting: agenda, decisions needed, open questions, "
                "and an editable message to request missing context.",
            )
            session.add(task)
            session.flush()
            put_evidence(session, task, source, origin="google_calendar")
        return task_view(session, task)


@router.post("/tasks/{task_id}/sync")
def sync_event(task_id: str, request: Request, user: User):
    with request.app.state.sessions() as session:
        event_id = owned_task(session, task_id, user.id).calendar_event_id
        if not event_id:
            raise HTTPException(409, "This workspace has no connected calendar event")
    data, grant = calendar.calendar_request(
        request.app.state.sessions, request.app.state.settings, user.id, event_id
    )
    with request.app.state.sessions.begin() as session:
        calendar.check_grant(session, user.id, grant, lock=True)
        task = owned_task(session, task_id, user.id, lock=True)
        item = session.scalar(
            select(Evidence).where(
                Evidence.task_id == task.id, Evidence.origin == "google_calendar"
            )
        )
        if not item or task.calendar_event_id != event_id:
            raise HTTPException(409, "Calendar access changed; reload this workspace")
        if data.get("status") == "cancelled":
            item.removed = True
            task.title = "Cancelled meeting"
            task.calendar_event_id = None
            task.generation += 1
        else:
            source = calendar.event_evidence(data)
            put_evidence(session, task, source, item=item)
            task.title = source.title
        return task_view(session, task)


@router.get("/tasks")
def tasks(request: Request, user: User):
    with request.app.state.sessions() as session:
        return [
            task_view(session, task)
            for task in session.scalars(
                select(Task)
                .where(Task.owner_id == user.id)
                .order_by(Task.created_at.desc())
                .limit(100)
            )
        ]


@router.post("/tasks", status_code=201)
def create_task(body: TaskInput, request: Request, user: User):
    with request.app.state.sessions.begin() as session:
        task = Task(owner_id=user.id, **body.model_dump())
        session.add(task)
        session.flush()
        return task_view(session, task)


@router.get("/tasks/{task_id}/workspace")
def workspace(task_id: str, request: Request, user: User):
    with request.app.state.sessions() as session:
        task = owned_task(session, task_id, user.id)
        snapshot = visible_snapshot(session, task.id)
        # Citations use the exact stored version, even while newer evidence is pending.
        citations = []
        if snapshot:
            for entry in snapshot.manifest:
                version = session.get(EvidenceVersion, entry["version_id"])
                citations.append(
                    {
                        **entry,
                        "title": version.title,
                        "content": version.content,
                        "url": version.url,
                    }
                )
        return {
            "task": task_view(session, task),
            "evidence": evidence_packet(session, task.id),
            "snapshot": {
                "id": snapshot.id,
                "brief": snapshot.brief,
                "draft": snapshot.draft,
                "created_at": snapshot.created_at,
                "citations": citations,
            }
            if snapshot
            else None,
        }


@router.post("/tasks/{task_id}/lifecycle")
def change_lifecycle(task_id: str, body: LifecycleInput, request: Request, user: User):
    with request.app.state.sessions.begin() as session:
        task = owned_task(session, task_id, user.id, lock=True)
        if (
            task.generation != body.expected_generation
            or task.completed_at != body.expected_completed_at
        ):
            raise HTTPException(
                409, "Workspace changed elsewhere; reload before updating its status"
            )
        if body.action == "review":
            snapshot = visible_snapshot(session, task_id)
            if (
                not snapshot
                or snapshot.generation != task.generation
                or snapshot.id != body.snapshot_id
                or snapshot.draft != body.expected_draft
            ):
                raise HTTPException(
                    409, "Brief or saved draft changed; review the current version first"
                )
            if task.reviewed_snapshot_id != snapshot.id or task.reviewed_at is None:
                task.reviewed_snapshot_id = snapshot.id
                task.reviewed_at = time.time()
        elif body.action == "complete":
            if task.completed_at is None:
                task.completed_at = time.time()
                task.completed_generation = task.generation
        else:
            task.completed_at = None
            task.completed_generation = None
        session.flush()
        return task_view(session, task)


@router.post("/tasks/{task_id}/evidence", status_code=201)
def add_evidence(task_id: str, body: EvidenceInput, request: Request, user: User):
    with request.app.state.sessions.begin() as session:
        task = owned_task(session, task_id, user.id, lock=True)
        return {"id": put_evidence(session, task, body).id}


@router.put("/tasks/{task_id}/evidence/{evidence_id}")
def edit_evidence(
    task_id: str, evidence_id: str, body: EvidenceInput, request: Request, user: User
):
    with request.app.state.sessions.begin() as session:
        task = owned_task(session, task_id, user.id, lock=True)
        item = session.get(Evidence, evidence_id)
        if not item or item.task_id != task.id or item.removed:
            raise HTTPException(404, "Evidence not found")
        if item.origin != "manual":
            raise HTTPException(409, "Refresh this connected source instead")
        return {"id": put_evidence(session, task, body, item=item).id}


@router.delete("/tasks/{task_id}/evidence/{evidence_id}", status_code=204)
def remove_evidence(task_id: str, evidence_id: str, request: Request, user: User):
    with request.app.state.sessions.begin() as session:
        task = owned_task(session, task_id, user.id, lock=True)
        item = session.get(Evidence, evidence_id)
        if not item or item.task_id != task.id:
            raise HTTPException(404, "Evidence not found")
        if not item.removed:
            item.removed = True
            task.generation += 1
        if item.origin == "google_calendar":
            task.calendar_event_id = None


@router.post("/tasks/{task_id}/prepare", status_code=202)
def prepare(task_id: str, request: Request, user: User):
    settings = request.app.state.settings
    if not settings.allow_model_requests or not settings.model_api_key.get_secret_value():
        raise HTTPException(
            503, "Meta preparation is disabled until credits and access are verified"
        )
    with request.app.state.sessions.begin() as session:
        task = owned_task(session, task_id, user.id, lock=True)
        if not evidence_packet(session, task.id):
            raise HTTPException(422, "Add some context before preparing this workspace")
        job = session.scalar(
            select(Job).where(Job.task_id == task.id, Job.generation == task.generation)
        )
        if not job:
            job = Job(task_id=task.id, generation=task.generation)
            session.add(job)
            session.flush()
        elif job.status == "failed" and job.attempts < 3:
            job.status, job.error_code, job.available_at = "queued", None, time.time()
        return job_view(job)


@router.get("/jobs/{job_id}")
def job_status(job_id: str, request: Request, user: User):
    with request.app.state.sessions() as session:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Preparation not found")
        owned_task(session, job.task_id, user.id)
        return job_view(job)


@router.put("/tasks/{task_id}/draft")
def save_draft(task_id: str, body: DraftInput, request: Request, user: User, snapshot_id: str):
    with request.app.state.sessions.begin() as session:
        task = owned_task(session, task_id, user.id, lock=True)
        snapshot = visible_snapshot(session, task_id)
        if not snapshot or snapshot.id != snapshot_id:
            raise HTTPException(
                409, "The brief changed or source access was removed. Your edits were not saved."
            )
        if snapshot.draft != body.expected_draft and snapshot.draft != body.draft:
            raise HTTPException(
                409,
                "The saved draft changed elsewhere. "
                "Your edits were not saved; compare the latest draft.",
            )
        if snapshot.draft != body.draft:
            task.reviewed_snapshot_id = None
            task.reviewed_at = None
            snapshot.draft = body.draft
        return {"saved": True}
