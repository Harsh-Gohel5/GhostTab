import json

import evaluate_meta
import pytest
import test_workspaces
from connector_samples import SampleModel

from ghosttab_api.models import Budget
from ghosttab_api.worker import run_once

system = test_workspaces.system


def test_evaluation_reservation_reconciles_in_main_ledger_without_live_model(
    system, monkeypatch, tmp_path
):
    monkeypatch.setattr(
        evaluate_meta,
        "run_once",
        lambda factory, settings: run_once(factory, settings, SampleModel()),
    )
    report_path = tmp_path / "report.json"
    evaluate_meta.evaluate(system.settings, system.factory, report_path)
    report = json.loads(report_path.read_text())
    assert len(report["cases"]) == 5
    assert all(item["status"] == "succeeded" for item in report["cases"])
    with system.factory() as session:
        assert session.get(Budget, 1).charged_microusd == round(
            report["estimated_total_usd"] * 1_000_000
        )
    assert system.request("GET", "/tasks").json() == []


def test_evaluation_does_not_bypass_existing_budget(system, tmp_path):
    with system.factory.begin() as session:
        session.get(Budget, 1).charged_microusd = 900_000
    with pytest.raises(SystemExit, match="exceed"):
        evaluate_meta.evaluate(system.settings, system.factory, tmp_path / "report.json")
    with system.factory() as session:
        assert session.get(Budget, 1).charged_microusd == 900_000


def test_custom_evaluation_keeps_the_same_budget_and_worker_validation(
    system, monkeypatch, tmp_path
):
    from evaluate_jira import CASES, workflow_sources

    monkeypatch.setattr(
        evaluate_meta,
        "run_once",
        lambda factory, settings: run_once(factory, settings, SampleModel()),
    )
    path = tmp_path / "jira.json"
    evaluate_meta.evaluate(
        system.settings,
        system.factory,
        path,
        cases=CASES,
        evidence_builder=workflow_sources,
        task_title="Fictional Jira task",
    )
    report = json.loads(path.read_text())
    assert [case["case"] for case in report["cases"]] == ["jira_conflict", "jira_revision"]
    assert all(case["status"] == "succeeded" for case in report["cases"])
    with system.factory() as session:
        assert session.get(Budget, 1).charged_microusd == round(
            report["estimated_total_usd"] * 1_000_000
        )


def test_device_profile_name_is_only_exposed_in_local_mode(system, monkeypatch):
    monkeypatch.setattr("ghosttab_api.routes.getpass.getuser", lambda: "Fictional Person")
    assert system.request("GET", "/config").json()["display_name"] == "Fictional Person"
    system.settings.auth_mode = "supabase"
    assert system.request("GET", "/config").json()["display_name"] == ""


def test_teams_evaluation_uses_fictional_sources_and_budgeted_worker(system, monkeypatch, tmp_path):
    from evaluate_teams import CASES, sources

    monkeypatch.setattr(
        evaluate_meta,
        "run_once",
        lambda factory, settings: run_once(factory, settings, SampleModel()),
    )
    path = tmp_path / "teams.json"
    evaluate_meta.evaluate(
        system.settings,
        system.factory,
        path,
        cases=CASES,
        evidence_builder=sources,
        task_title="Fictional Teams task",
    )
    report = json.loads(path.read_text())
    assert len(report["cases"]) == 2
    assert all(case["status"] == "succeeded" for case in report["cases"])
