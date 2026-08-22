"""Integracion WorkItemTask -> workload: las horas estimadas suman a assigned_hours,
igual que ya hacen las horas de tickets (apps.tickets)."""
from decimal import Decimal

import pytest

from apps.resources.services import employee_workload
from tests.factories import EmployeeFactory, WorkItemTaskFactory, task_status

pytestmark = pytest.mark.django_db


def _row(emp):
    rows = employee_workload()
    return next(r for r in rows if r["employee_id"] == str(emp.id))


def test_workitem_task_hours_add_to_assigned(db):
    emp = EmployeeFactory()
    WorkItemTaskFactory(assignee=emp, estimated_hours=Decimal("5.00"))
    row = _row(emp)
    assert row["workitem_hours"] == 5.0
    assert row["assigned_hours"] == 5.0
    assert row["open_workitem_tasks"] == 1


def test_done_workitem_task_excluded(db):
    emp = EmployeeFactory()
    WorkItemTaskFactory(assignee=emp, estimated_hours=Decimal("5.00"),
                        status=task_status("DONE", is_closed=True))
    row = _row(emp)
    assert row["workitem_hours"] == 0.0
    assert row["open_workitem_tasks"] == 0


def test_unassigned_workitem_task_ignored(db):
    emp = EmployeeFactory()
    WorkItemTaskFactory(assignee=None, estimated_hours=Decimal("5.00"))
    row = _row(emp)
    assert row["workitem_hours"] == 0.0


def test_workitem_and_task_hours_combine(db):
    from apps.resources.models import TaskAssignment
    from tests.factories import TaskFactory

    emp = EmployeeFactory()
    task = TaskFactory(estimated_hours=Decimal("10.00"), status=task_status("IN_PROGRESS"))
    TaskAssignment.objects.create(task=task, employee=emp, legacy_code="ASG-901")
    WorkItemTaskFactory(assignee=emp, estimated_hours=Decimal("5.00"))

    row = _row(emp)
    assert row["assigned_hours"] == 15.0
    assert row["workitem_hours"] == 5.0


def test_employee_without_workitems_unaffected(db):
    emp = EmployeeFactory()
    row = _row(emp)
    assert row["workitem_hours"] == 0.0
    assert row["open_workitem_tasks"] == 0
