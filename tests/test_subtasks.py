import pytest

from apps.projects.models import SubTask
from tests.factories import TaskFactory, sev

pytestmark = pytest.mark.django_db


def _action_status(code="PENDING"):
    from apps.catalogs.models import ActionStatus
    return ActionStatus.objects.get_or_create(code=code, defaults={"name": code})[0]


def test_subtask_create_autogenerates_code(pm_client):
    task = TaskFactory()
    body = {"task": str(task.id), "description": "no está logeando bien",
            "status": _action_status().code, "priority": sev().code}
    resp = pm_client.post("/api/subtasks/", body, format="json")
    assert resp.status_code == 201, resp.content
    assert resp.json()["legacy_code"] == "SUB-001"
    assert resp.json()["task_name"] == task.name


def test_subtask_filters_by_project(pm_client):
    task = TaskFactory()
    other = TaskFactory()
    SubTask.objects.create(task=task, description="a", status=_action_status())
    SubTask.objects.create(task=other, description="b", status=_action_status())
    resp = pm_client.get(f"/api/subtasks/?project={task.project_id}")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
