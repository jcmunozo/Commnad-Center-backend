import pytest

from apps.projects.services import weighted_progress
from tests.factories import TaskFactory, task_status

pytestmark = pytest.mark.django_db


def test_project_str_includes_legacy_code():
    task = TaskFactory(legacy_code="TSK-001")
    assert "TSK-001" in str(task)


def test_soft_delete_hides_from_active_manager():
    task = TaskFactory()
    from apps.projects.models import Task

    assert Task.active.filter(pk=task.pk).exists()
    task.soft_delete()
    assert not Task.active.filter(pk=task.pk).exists()
    assert Task.objects.filter(pk=task.pk).exists()  # still there physically


def test_weighted_progress_uses_estimated_hours():
    in_progress = task_status("IN_PROGRESS")
    t1 = TaskFactory(status=in_progress, estimated_hours=30, progress_pct="1.0")
    TaskFactory(project=t1.project, status=in_progress, estimated_hours=10, progress_pct="0.0")
    # weighted = (30*1 + 10*0) / 40 = 0.75
    result = weighted_progress(t1.project)
    assert result["weighted_progress_pct"] == 0.75
    assert result["task_count"] == 2
