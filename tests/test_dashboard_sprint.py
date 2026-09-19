"""Sprint-scoped Dashboard: PortfolioDashboardView/AlertsView ?sprint_id=,
plus the new Burndown and Velocity endpoints."""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.projects.models import Milestone, MilestoneTask, Sprint, SubTask
from apps.projects.selectors import sprint_scope_q
from tests.factories import ProjectFactory, SprintFactory, TaskFactory, sev, task_status
from tests.test_subtasks import _action_status

pytestmark = pytest.mark.django_db


def _done_status():
    return task_status("DONE", is_closed=True)


# --- sprint_scope_q ---

def test_sprint_scope_q_active_includes_carried_over_open_task():
    old_sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    active_sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    carried_over = TaskFactory(sprint=old_sprint, status=task_status("TODO"))
    in_active = TaskFactory(sprint=active_sprint, status=task_status("TODO"))
    TaskFactory(sprint=old_sprint, status=_done_status())  # closed -> excluded

    ids = set(type(carried_over).objects.filter(sprint_scope_q(active_sprint)).values_list("id", flat=True))
    assert carried_over.id in ids
    assert in_active.id in ids
    assert len(ids) == 2


def test_sprint_scope_q_closed_is_strict_match():
    closed_sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    other_closed = SprintFactory(status=Sprint.STATUS_CLOSED)
    in_scope = TaskFactory(sprint=closed_sprint, status=task_status("TODO"))
    TaskFactory(sprint=other_closed, status=task_status("TODO"))

    ids = set(type(in_scope).objects.filter(sprint_scope_q(closed_sprint)).values_list("id", flat=True))
    assert ids == {in_scope.id}


# --- PortfolioDashboardView ---

def test_portfolio_dashboard_without_sprint_id_is_unscoped(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    TaskFactory(sprint=sprint, estimated_hours=5)
    TaskFactory(sprint=None, estimated_hours=3)
    resp = pm_client.get("/api/dashboard/portfolio/")
    assert resp.status_code == 200
    assert resp.data["open_tasks"] == 2
    assert "sprint" not in resp.data


def test_portfolio_dashboard_scopes_tasks_to_sprint(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    other_project_task = TaskFactory(sprint=sprint, estimated_hours=5, actual_hours=2)
    TaskFactory(sprint=None, estimated_hours=3)  # not in sprint

    resp = pm_client.get(f"/api/dashboard/portfolio/?sprint_id={sprint.id}")
    assert resp.status_code == 200
    assert resp.data["open_tasks"] == 1
    assert resp.data["sprint"]["id"] == str(sprint.id)
    assert resp.data["sprint_effort_totals"] == {"estimated_hours": 5.0, "actual_hours": 2.0}
    assert [t["id"] for t in resp.data["tasks_effort"]] == [str(other_project_task.id)]


def test_portfolio_dashboard_projects_stay_unscoped_by_sprint(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    TaskFactory(sprint=sprint)
    ProjectFactory()  # unrelated project, no tasks in sprint at all

    unscoped = pm_client.get("/api/dashboard/portfolio/").data
    scoped = pm_client.get(f"/api/dashboard/portfolio/?sprint_id={sprint.id}").data
    assert scoped["total_projects"] == unscoped["total_projects"]
    assert scoped["by_status"] == unscoped["by_status"]


def test_portfolio_dashboard_bad_sprint_id_404s(pm_client):
    resp = pm_client.get("/api/dashboard/portfolio/?sprint_id=00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# --- AlertsView ---

def test_alerts_scopes_overdue_subtasks_to_sprint(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    in_sprint_task = TaskFactory(sprint=sprint)
    out_of_sprint_task = TaskFactory(sprint=None)
    yesterday = timezone.now() - timedelta(days=1)
    SubTask.objects.create(task=in_sprint_task, description="in", due_date=yesterday,
                            status=_action_status())
    SubTask.objects.create(task=out_of_sprint_task, description="out", due_date=yesterday,
                            status=_action_status())

    resp = pm_client.get(f"/api/dashboard/alerts/?sprint_id={sprint.id}")
    assert resp.status_code == 200
    descriptions = {s["description"] for s in resp.data["overdue_subtasks"]}
    assert descriptions == {"in"}


def test_alerts_scopes_milestones_via_linked_task_heuristic(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    in_sprint_task = TaskFactory(sprint=sprint, status=task_status("TODO"))
    out_of_sprint_task = TaskFactory(sprint=None, status=task_status("TODO"))
    yesterday = timezone.now() - timedelta(days=1)

    linked_milestone = Milestone.objects.create(
        project=in_sprint_task.project, name="In sprint", target_date=yesterday)
    MilestoneTask.objects.create(milestone=linked_milestone, task=in_sprint_task)

    unlinked_milestone = Milestone.objects.create(
        project=out_of_sprint_task.project, name="Out of sprint", target_date=yesterday)
    MilestoneTask.objects.create(milestone=unlinked_milestone, task=out_of_sprint_task)

    resp = pm_client.get(f"/api/dashboard/alerts/?sprint_id={sprint.id}")
    assert resp.status_code == 200
    names = {m["name"] for m in resp.data["overdue_milestones"]}
    assert names == {"In sprint"}


# --- BurndownView ---

def test_burndown_requires_sprint_id(pm_client):
    resp = pm_client.get("/api/dashboard/burndown/")
    assert resp.status_code == 400


def test_burndown_empty_sprint_returns_no_days(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    resp = pm_client.get(f"/api/dashboard/burndown/?sprint_id={sprint.id}")
    assert resp.status_code == 200
    assert resp.data["total_scope_hours"] == 0.0
    assert resp.data["days"] == []


def test_burndown_computes_remaining_and_ideal_hours(pm_client):
    today = timezone.localdate()
    sprint = SprintFactory(
        status=Sprint.STATUS_ACTIVE, start_date=today - timedelta(days=4), end_date=today)
    done_early = TaskFactory(sprint=sprint, estimated_hours=4,
                              status=_done_status())
    done_early.completed_at = timezone.now() - timedelta(days=3)
    done_early.save(update_fields=["completed_at"])
    still_open = TaskFactory(sprint=sprint, estimated_hours=6, status=task_status("TODO"))

    resp = pm_client.get(f"/api/dashboard/burndown/?sprint_id={sprint.id}")
    assert resp.status_code == 200
    assert resp.data["total_scope_hours"] == 10.0
    days = {d["date"]: d for d in resp.data["days"]}
    first_day = (today - timedelta(days=4)).isoformat()
    last_day = today.isoformat()
    assert days[first_day]["remaining_hours"] == 10.0  # nothing completed yet on day 0
    assert days[last_day]["remaining_hours"] == 6.0  # done_early's 4h dropped off
    assert days[first_day]["ideal_hours"] == 10.0
    assert days[last_day]["ideal_hours"] == 0.0
    assert still_open.estimated_hours == 6  # sanity: still counted in total scope


# --- VelocityView ---

def test_velocity_only_counts_done_tasks_in_closed_sprints(pm_client):
    closed = SprintFactory(status=Sprint.STATUS_CLOSED, name="Sprint A")
    active = SprintFactory(status=Sprint.STATUS_ACTIVE, name="Sprint B")
    TaskFactory(sprint=closed, status=_done_status(), estimated_hours=5, actual_hours=6)
    TaskFactory(sprint=closed, status=task_status("TODO"), estimated_hours=99)  # not DONE
    TaskFactory(sprint=active, status=_done_status(), estimated_hours=100)  # active, not closed

    resp = pm_client.get("/api/dashboard/velocity/")
    assert resp.status_code == 200
    assert len(resp.data["sprints"]) == 1
    row = resp.data["sprints"][0]
    assert row["id"] == str(closed.id)
    assert row["tasks_done"] == 1
    assert row["estimated_hours"] == 5.0
    assert row["hours_done"] == 5.0
    assert row["actual_hours"] == 6.0


def test_velocity_respects_limit_and_chronological_order(pm_client):
    for i in range(3):
        SprintFactory(status=Sprint.STATUS_CLOSED, name=f"Sprint {i}",
                      start_date=timezone.localdate() - timedelta(days=(3 - i) * 14))

    resp = pm_client.get("/api/dashboard/velocity/?limit=2")
    assert resp.status_code == 200
    names = [s["name"] for s in resp.data["sprints"]]
    assert names == ["Sprint 1", "Sprint 2"]  # oldest-to-newest of the last 2


def test_velocity_no_closed_sprints_returns_empty_list(pm_client):
    SprintFactory(status=Sprint.STATUS_ACTIVE)
    resp = pm_client.get("/api/dashboard/velocity/")
    assert resp.status_code == 200
    assert resp.data == {"sprints": []}
