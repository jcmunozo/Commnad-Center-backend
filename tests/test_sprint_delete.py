"""Deleting a sprint created by mistake: mandatory reason, tasks detached,
and no lingering ACTIVE row blocking the next sprint."""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.core.permissions import ROLE_TEAM
from apps.projects.models import Sprint
from tests.factories import SprintFactory, TaskFactory, WorkItemTaskFactory, task_status

pytestmark = pytest.mark.django_db

REASON = {"reason": "Created by mistake"}


def _url(sprint):
    return f"/api/sprints/{sprint.id}/"


def test_reason_is_required(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    assert pm_client.delete(_url(sprint)).status_code == 400
    assert pm_client.delete(_url(sprint), {"reason": "no"}, format="json").status_code == 400
    assert pm_client.delete(_url(sprint), {"reason": "x" * 91}, format="json").status_code == 400
    sprint.refresh_from_db()
    assert sprint.is_active


def test_delete_closed_sprint_detaches_tasks(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    task = TaskFactory(sprint=sprint)
    ci_task = WorkItemTaskFactory(sprint=sprint)

    resp = pm_client.delete(_url(sprint), REASON, format="json")

    assert resp.status_code == 200
    assert resp.json()["detached_tasks"] == 1
    assert resp.json()["detached_ci_tasks"] == 1
    assert resp.json()["was_active"] is False
    sprint.refresh_from_db()
    task.refresh_from_db()
    ci_task.refresh_from_db()
    assert sprint.is_active is False
    assert task.sprint is None and ci_task.sprint is None
    assert task.is_active  # the task itself is untouched


def test_delete_active_sprint_does_not_block_next_one(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)

    resp = pm_client.delete(_url(sprint), REASON, format="json")

    assert resp.status_code == 200 and resp.json()["was_active"] is True
    assert pm_client.get("/api/sprints/active/").data is None
    created = pm_client.post(
        "/api/sprints/",
        {"name": "Fixed", "start_date": "2030-01-01", "end_date": "2030-01-14"}, format="json")
    assert created.status_code == 201


def test_reason_is_stored_in_history(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    pm_client.delete(_url(sprint), {"reason": "Wrong dates"}, format="json")
    assert sprint.history.first().history_change_reason == "Deleted: Wrong dates"


def test_deleted_sprint_leaves_lists_and_velocity(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    TaskFactory(sprint=sprint, status=task_status("DONE", is_closed=True))
    pm_client.delete(_url(sprint), REASON, format="json")

    ids = [s["id"] for s in pm_client.get("/api/sprints/").json()["results"]]
    assert str(sprint.id) not in ids
    velocity = pm_client.get("/api/dashboard/velocity/").json()["sprints"]
    assert velocity == []


def test_second_delete_is_404(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    assert pm_client.delete(_url(sprint), REASON, format="json").status_code == 200
    assert pm_client.delete(_url(sprint), REASON, format="json").status_code == 404


def test_viewer_and_team_cannot_delete(viewer_client):
    sprint = SprintFactory(status=Sprint.STATUS_CLOSED)
    assert viewer_client.delete(_url(sprint), REASON, format="json").status_code == 403

    user = get_user_model().objects.create_user(username="team_member", password="x")
    user.groups.add(Group.objects.get_or_create(name=ROLE_TEAM)[0])
    client = APIClient()  # fresh instance: the fixtures share one api_client
    client.force_authenticate(user)
    assert client.delete(_url(sprint), REASON, format="json").status_code == 403
    sprint.refresh_from_db()
    assert sprint.is_active


def test_deletion_impact_counts_open_work(pm_client):
    sprint = SprintFactory(status=Sprint.STATUS_ACTIVE)
    TaskFactory(sprint=sprint, status=task_status("TODO"))
    TaskFactory(sprint=sprint, status=task_status("DONE", is_closed=True))
    WorkItemTaskFactory(sprint=sprint, status=task_status("IN_PROGRESS"))

    data = pm_client.get(f"/api/sprints/{sprint.id}/deletion_impact/").json()

    assert data == {"tasks": 2, "open_tasks": 1, "ci_tasks": 1, "open_ci_tasks": 1,
                    "is_active_sprint": True}


def test_deletion_impact_forbidden_for_viewer(viewer_client):
    sprint = SprintFactory()
    assert viewer_client.get(f"/api/sprints/{sprint.id}/deletion_impact/").status_code == 403
