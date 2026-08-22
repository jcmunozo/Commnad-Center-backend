import pytest

from apps.workitems.models import WorkItem
from tests.factories import (
    EmployeeFactory,
    ProjectFactory,
    WorkItemFactory,
    WorkItemTaskFactory,
    project_status,
    sev,
    task_status,
)

pytestmark = pytest.mark.django_db


def _wi_body(**overrides):
    body = {"title": "Documentacion CI/CD", "status": project_status().code,
            "priority": sev().code}
    body.update(overrides)
    return body


def test_create_autogenerates_code(pm_client):
    resp = pm_client.post("/api/work-items/", _wi_body(), format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["legacy_code"] == "WKI-001"
    assert data["project"] is None


def test_create_with_project_traces_it(pm_client):
    project = ProjectFactory()
    resp = pm_client.post("/api/work-items/", _wi_body(project=str(project.id)), format="json")
    assert resp.status_code == 201, resp.content
    detail = pm_client.get(f"/api/work-items/{resp.json()['id']}/").json()
    assert detail["project"] == str(project.id)


def test_team_member_can_create(api_client, django_user_model):
    from django.contrib.auth.models import Group

    from apps.core.permissions import ROLE_TEAM

    user = django_user_model.objects.create_user(username="dev1", password="x")
    group, _ = Group.objects.get_or_create(name=ROLE_TEAM)
    user.groups.add(group)
    api_client.force_authenticate(user)
    resp = api_client.post("/api/work-items/", _wi_body(), format="json")
    assert resp.status_code == 201, resp.content


def test_viewer_cannot_write(api_client, pm_user, viewer_user):
    api_client.force_authenticate(pm_user)
    wi_id = api_client.post("/api/work-items/", _wi_body(), format="json").json()["id"]

    api_client.force_authenticate(viewer_user)
    assert api_client.post("/api/work-items/", _wi_body(), format="json").status_code == 403
    assert api_client.patch(f"/api/work-items/{wi_id}/", {"title": "x"},
                            format="json").status_code == 403
    assert api_client.get("/api/work-items/").status_code == 200


def test_delete_is_soft(pm_client):
    wi_id = pm_client.post("/api/work-items/", _wi_body(), format="json").json()["id"]
    assert pm_client.delete(f"/api/work-items/{wi_id}/").status_code == 204
    assert WorkItem.objects.get(pk=wi_id).is_active is False
    assert pm_client.get("/api/work-items/").json()["count"] == 0


def test_filters_and_search(pm_client):
    project = ProjectFactory()
    pm_client.post("/api/work-items/", _wi_body(project=str(project.id)), format="json")
    pm_client.post("/api/work-items/", _wi_body(title="Estandares de logging"), format="json")

    assert pm_client.get(f"/api/work-items/?project={project.id}").json()["count"] == 1
    assert pm_client.get("/api/work-items/?search=logging").json()["count"] == 1


# ----------------------------- WorkItemTask -----------------------------
def _task_body(work_item, **overrides):
    body = {"work_item": str(work_item.id), "name": "Explicar flujo",
            "status": task_status().code, "priority": sev().code,
            "estimated_hours": "3.00"}
    body.update(overrides)
    return body


def test_task_autogenerates_code_and_links_workitem(pm_client):
    wi = WorkItemFactory()
    resp = pm_client.post("/api/work-item-tasks/", _task_body(wi), format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["legacy_code"] == "WIT-001"

    listed = pm_client.get(f"/api/work-item-tasks/?work_item={wi.id}").json()
    assert listed["count"] == 1
    assert listed["results"][0]["work_item_title"] == wi.title


def test_task_assignee_and_hours(pm_client):
    wi = WorkItemFactory()
    emp = EmployeeFactory()
    resp = pm_client.post("/api/work-item-tasks/",
                          _task_body(wi, assignee=str(emp.id)), format="json")
    assert resp.status_code == 201, resp.content
    detail = pm_client.get(f"/api/work-item-tasks/{resp.json()['id']}/").json()
    assert detail["assignee"] == str(emp.id)
    assert detail["estimated_hours"] == "3.00"


# ----------------------------- WorkItemMilestone -----------------------------
def _milestone_body(work_item, **overrides):
    body = {"work_item": str(work_item.id), "name": "Entrega a equipo de soporte"}
    body.update(overrides)
    return body


def test_milestone_optional_and_progress_derives_from_tasks(pm_client):
    wi = WorkItemFactory()
    # a WorkItem with no milestone at all is valid — created above, no assertion needed
    resp = pm_client.post("/api/work-item-milestones/", _milestone_body(wi), format="json")
    assert resp.status_code == 201, resp.content
    milestone_id = resp.json()["id"]
    assert resp.json()["progress"]["derived_status"] == "PENDING"

    t1 = WorkItemTaskFactory(work_item=wi, status=task_status("TODO"))
    t2 = WorkItemTaskFactory(work_item=wi, status=task_status("TODO"))
    pm_client.post(f"/api/work-item-milestones/{milestone_id}/tasks/",
                   {"task": str(t1.id)}, format="json")
    pm_client.post(f"/api/work-item-milestones/{milestone_id}/tasks/",
                   {"task": str(t2.id)}, format="json")

    mid_progress = pm_client.get(f"/api/work-item-milestones/{milestone_id}/").json()["progress"]
    assert mid_progress["total_tasks"] == 2
    assert mid_progress["derived_status"] == "IN_PROGRESS"

    t1.status = task_status("DONE", is_closed=True)
    t1.save()
    t2.status = task_status("DONE", is_closed=True)
    t2.save()
    done_progress = pm_client.get(f"/api/work-item-milestones/{milestone_id}/").json()["progress"]
    assert done_progress["derived_status"] == "COMPLETED"
