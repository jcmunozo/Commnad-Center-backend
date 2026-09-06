"""Archived (soft-deleted) tasks stay out of the default /api/tasks/ list,
but a search should still surface a match, and a direct fetch by id must
still work for one reached that way — same rule as projects."""
import pytest

from tests.factories import TaskFactory

pytestmark = pytest.mark.django_db


def test_archived_task_excluded_from_default_list(pm_client):
    task = TaskFactory(name="Retired migration script")
    task.soft_delete()
    codes = [t["legacy_code"] for t in pm_client.get("/api/tasks/").data["results"]]
    assert task.legacy_code not in codes


def test_archived_task_surfaces_in_search(pm_client):
    task = TaskFactory(name="Retired migration script")
    task.soft_delete()
    resp = pm_client.get("/api/tasks/", {"search": "Retired migration script"})
    codes = [t["legacy_code"] for t in resp.data["results"]]
    assert task.legacy_code in codes
    assert resp.data["results"][0]["is_active"] is False


def test_archived_task_still_retrievable_by_id(pm_client):
    task = TaskFactory()
    task.soft_delete()
    resp = pm_client.get(f"/api/tasks/{task.id}/")
    assert resp.status_code == 200
    assert resp.data["is_active"] is False
