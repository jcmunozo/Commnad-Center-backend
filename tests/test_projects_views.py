import pytest

from tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


def test_list_projects_requires_auth(api_client):
    resp = api_client.get("/api/projects/")
    assert resp.status_code == 401


def test_viewer_can_list_but_not_create(viewer_client):
    ProjectFactory()
    assert viewer_client.get("/api/projects/").status_code == 200
    resp = viewer_client.post("/api/projects/", {"name": "New"}, format="json")
    assert resp.status_code == 403  # viewer lacks write role


def test_pm_can_create_project(pm_client):
    project = ProjectFactory()
    payload = {
        "name": "PM Project",
        "project_type": project.project_type_id,
        "status": project.status_id,
        "priority": project.priority_id,
    }
    resp = pm_client.post("/api/projects/", payload, format="json")
    assert resp.status_code == 201, resp.content


def test_project_dashboard_action(pm_client):
    project = ProjectFactory()
    resp = pm_client.get(f"/api/projects/{project.id}/dashboard/")
    assert resp.status_code == 200
    assert resp.data["open_tasks"] == 0
