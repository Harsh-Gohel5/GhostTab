from types import SimpleNamespace

import test_workspaces

from ghosttab_api.auth import Principal, current_user
from ghosttab_api.source_changes import source_changes
from ghosttab_api.worker import run_once

system = test_workspaces.system


def test_uncited_source_updates_do_not_invent_claim_dependencies():
    before = {"id": "doc", "version_id": "old", "title": "Doc", "content": "Old", "url": ""}
    current = {**before, "version_id": "new", "content": "New", "origin": "google_docs"}
    point = {
        "text": "Unchanged calendar timing",
        "citations": [{"evidence_id": "calendar", "quote": "Noon"}],
    }
    snapshot = SimpleNamespace(brief={"summary": point, "facts": [], "next_steps": []})
    change = source_changes([current], snapshot, [before])[0]
    assert change["claims_to_review"] == []


def prepared(system):
    task, evidence = test_workspaces.seeded(system)
    system.request("POST", f"/tasks/{task}/prepare")
    model = test_workspaces.FakeModel()
    assert run_once(system.factory, system.settings, model)
    return task, evidence, model


def test_comparison_uses_brief_baseline_across_multiple_edits_and_clears_after_update(system):
    task, evidence, model = prepared(system)
    before = system.request("GET", f"/tasks/{task}/workspace").json()
    assert before["source_changes"] == []
    for day in ("Friday", "Saturday"):
        assert (
            system.request(
                "PUT",
                f"/tasks/{task}/evidence/{evidence}",
                {"title": "Updated request", "content": f"Review the launch plan on {day}."},
            ).status_code
            == 200
        )
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["snapshot"] == before["snapshot"]
    assert data["task"]["freshness"] == "stale"
    assert len(data["source_changes"]) == 1
    change = data["source_changes"][0]
    assert change["kind"] == "updated"
    assert change["previous"]["content"] == "Review the launch plan on Thursday."
    assert change["current"]["content"] == "Review the launch plan on Saturday."
    assert change["changed_fields"] == ["title", "content", "url"]
    assert [p["section"] for p in change["claims_to_review"]] == ["summary", "fact", "next_step"]
    assert all(p["quotes"] == [change["previous"]["content"]] for p in change["claims_to_review"])
    assert model.calls == 1  # Reads/comparison never enqueue or submit inference.
    system.request("POST", f"/tasks/{task}/prepare")
    assert run_once(system.factory, system.settings, model)
    updated = system.request("GET", f"/tasks/{task}/workspace").json()
    assert updated["source_changes"] == []
    assert updated["task"]["freshness"] == "current"


def test_added_context_is_distinct_from_changed_claims_and_no_baseline_stays_empty(system):
    task, _, model = prepared(system)
    added = system.request(
        "POST", f"/tasks/{task}/evidence", {"title": "New note", "content": "Nina owns review."}
    ).json()["id"]
    change = system.request("GET", f"/tasks/{task}/workspace").json()["source_changes"][0]
    assert change["kind"] == "added" and change["current"]["id"] == added
    assert change["previous"] is None and change["claims_to_review"] == []
    assert model.calls == 1
    new_task, _ = test_workspaces.seeded(system)
    assert system.request("GET", f"/tasks/{new_task}/workspace").json()["source_changes"] == []


def test_metadata_only_updates_show_title_and_link_without_inventing_text_edits(system):
    task, evidence, _ = prepared(system)
    system.request(
        "PUT",
        f"/tasks/{task}/evidence/{evidence}",
        {
            "title": "Renamed request",
            "content": "Review the launch plan on Thursday.",
            "url": "https://example.com/renamed",
        },
    )
    change = system.request("GET", f"/tasks/{task}/workspace").json()["source_changes"][0]
    assert change["changed_fields"] == ["title", "url"]
    assert change["previous"]["content"] == change["current"]["content"]


def test_comparison_never_exposes_other_owners_or_removed_baselines(system):
    task, evidence, _ = prepared(system)
    system.request(
        "PUT", f"/tasks/{task}/evidence/{evidence}", {"title": "Changed", "content": "New source."}
    )
    system.app.dependency_overrides[current_user] = lambda: Principal("bob")
    assert system.request("GET", f"/tasks/{task}/workspace").status_code == 404
    system.app.dependency_overrides[current_user] = lambda: Principal("alice")
    system.request("DELETE", f"/tasks/{task}/evidence/{evidence}")
    data = system.request("GET", f"/tasks/{task}/workspace").json()
    assert data["source_changes"] == [] and data["snapshot"] is None


def test_unchanged_evidence_does_not_create_a_comparison(system):
    task, evidence, _ = prepared(system)
    system.request(
        "PUT",
        f"/tasks/{task}/evidence/{evidence}",
        {
            "title": "Meeting request",
            "content": "Review the launch plan on Thursday.",
            "url": "https://example.com/meeting",
        },
    )
    assert system.request("GET", f"/tasks/{task}/workspace").json()["source_changes"] == []
