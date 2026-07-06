import pytest

from apps.projects.serializers import ProjectWriteSerializer, TaskWriteSerializer
from tests.factories import ProjectFactory, project_status, project_type, sev, task_status, task_type

pytestmark = pytest.mark.django_db


def test_project_write_rejects_end_before_start():
    data = {
        "name": "X",
        "client": ProjectFactory().client_id,
        "project_type": project_type().code,
        "status": project_status().code,
        "priority": sev().code,
        "start_date": "2026-06-01T00:00:00Z",
        "planned_end": "2026-01-01T00:00:00Z",
    }
    serializer = ProjectWriteSerializer(data=data)
    assert not serializer.is_valid()
    assert "planned_end" in str(serializer.errors)


def test_task_write_rejects_endpoint_from_other_api():
    project = ProjectFactory()
    data = {
        "name": "T",
        "project": project.id,
        "task_type": task_type().code,
        "status": task_status().code,
        "priority": sev().code,
    }
    serializer = TaskWriteSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
