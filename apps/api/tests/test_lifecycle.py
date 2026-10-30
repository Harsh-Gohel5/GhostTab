import test_workspaces
from connector_samples import SampleModel

from ghosttab_api.auth import Principal, current_user
from ghosttab_api.worker import run_once

system = test_workspaces.system


def view(system, tid):
    return system.request("GET", f"/tasks/{tid}/workspace").json()


def change(system, workspace, action, **overrides):
    body = {
        "action": action,
        "expected_generation": workspace["task"]["generation"],
        "expected_completed_at": workspace["task"]["completed_at"],
        "snapshot_id": workspace["snapshot"]["id"] if workspace["snapshot"] else None,
        "expected_draft": workspace["snapshot"]["draft"] if workspace["snapshot"] else None,
        **overrides,
    }
    return system.request("POST", f"/tasks/{workspace['task']['id']}/lifecycle", body)


def prepared(system):
    tid, eid = test_workspaces.seeded(system)
    system.request("POST", f"/tasks/{tid}/prepare")
    assert run_once(system.factory, system.settings, SampleModel())
    return tid, eid, view(system, tid)


def test_review_complete_reopen_persist_without_changing_evidence_or_generation(system):
    tid, _, initial = prepared(system)
    assert initial["task"]["review_current"] is False
    reviewed = change(system, initial, "review")
    assert reviewed.status_code == 200 and reviewed.json()["review_current"]
    saved = view(system, tid)
    assert saved["snapshot"] == initial["snapshot"]
    assert saved["task"]["generation"] == initial["task"]["generation"]
    result = change(system, saved, "complete")
    assert result.json()["lifecycle"] == "completed"
    completed = view(system, tid)
    assert completed["task"]["review_current"]
    assert completed["task"]["completed_at"] is not None
    assert change(system, completed, "reopen").json()["lifecycle"] == "active"
    reopened = view(system, tid)
    assert reopened["task"]["completed_at"] is None
    assert reopened["task"]["review_current"]


def test_source_update_requires_review_again_but_does_not_reopen_completed_task(system):
    tid, eid, initial = prepared(system)
    change(system, initial, "review")
    change(system, view(system, tid), "complete")
    assert (
        system.request(
            "PUT",
            f"/tasks/{tid}/evidence/{eid}",
            {"title": "Meeting request", "content": "Review the launch plan on Friday.", "url": ""},
        ).status_code
        == 200
    )
    updated = view(system, tid)
    assert updated["task"]["lifecycle"] == "completed"
    assert updated["task"]["changed_since_completion"]
    assert not updated["task"]["review_current"]
    assert updated["task"]["reviewed_at"] is not None
    assert change(system, updated, "review").status_code == 409
    assert change(system, initial, "reopen").status_code == 409
    assert change(system, updated, "reopen").status_code == 200
    assert view(system, tid)["task"]["freshness"] == "stale"


def test_draft_edit_invalidates_review_and_old_tab_cannot_review_different_saved_draft(system):
    tid, _, initial = prepared(system)
    change(system, initial, "review")
    path = f"/tasks/{tid}/draft?snapshot_id={initial['snapshot']['id']}"
    old = initial["snapshot"]["draft"]
    assert (
        system.request("PUT", path, {"draft": old + " Updated.", "expected_draft": old}).status_code
        == 200
    )
    assert not view(system, tid)["task"]["review_current"]
    assert change(system, initial, "review").status_code == 409
    assert change(system, view(system, tid), "review").json()["review_current"]


def test_review_does_not_trim_saved_draft_and_identical_save_preserves_review(system):
    tid, _, initial = prepared(system)
    path = f"/tasks/{tid}/draft?snapshot_id={initial['snapshot']['id']}"
    whitespace = "  Review this draft.\n"
    system.request(
        "PUT", path, {"draft": whitespace, "expected_draft": initial["snapshot"]["draft"]}
    )
    saved = view(system, tid)
    assert change(system, saved, "review").status_code == 200
    system.request("PUT", path, {"draft": whitespace, "expected_draft": whitespace})
    assert view(system, tid)["task"]["review_current"]


def test_human_completion_needs_no_model_or_sources_and_conflicting_status_is_rejected(system):
    tid = system.request(
        "POST", "/tasks", {"title": "Manual task", "goal": "Finish independently"}
    ).json()["id"]
    initial = view(system, tid)
    assert change(system, initial, "review").status_code == 409
    assert change(system, initial, "complete").json()["lifecycle"] == "completed"
    assert change(system, initial, "reopen").status_code == 409
    assert change(system, view(system, tid), "reopen").status_code == 200
    assert view(system, tid)["task"]["job"] is None


def test_another_owner_and_removed_sources_cannot_mark_reviewed(system):
    tid, eid, initial = prepared(system)
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert change(system, initial, "complete").status_code == 404
    system.app.dependency_overrides[current_user] = lambda: Principal("alice")
    change(system, initial, "review")
    system.request("DELETE", f"/tasks/{tid}/evidence/{eid}")
    blocked = view(system, tid)
    assert blocked["snapshot"] is None and not blocked["task"]["review_current"]
    assert change(system, blocked, "review").status_code == 409
