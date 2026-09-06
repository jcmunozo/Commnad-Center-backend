"""Bug Fix tasks are reactive/unplanned work: they still count as an open task
so a dev's plate is visible, but their hours must not inflate assigned_hours/
workload_pct — that's the estimate the dev was actually staffed against."""
from decimal import Decimal

import pytest

from apps.resources.models import TaskAssignment
from apps.resources.services import employee_workload
from tests.factories import EmployeeFactory, TaskFactory, task_status, task_type

pytestmark = pytest.mark.django_db


def _row(emp):
    rows = employee_workload()
    return next(r for r in rows if r["employee_id"] == str(emp.id))


def test_bug_fix_task_excluded_from_assigned_hours():
    emp = EmployeeFactory()
    task = TaskFactory(estimated_hours=Decimal("8.00"), status=task_status("IN_PROGRESS"),
                       task_type=task_type("BUG_FIX"))
    TaskAssignment.objects.create(task=task, employee=emp, legacy_code="ASG-910")

    row = _row(emp)
    assert row["assigned_hours"] == 0.0
    assert row["open_tasks"] == 1  # still shown as work in flight


def test_bug_fix_task_does_not_dilute_other_tasks_hours():
    emp = EmployeeFactory()
    dev_task = TaskFactory(estimated_hours=Decimal("10.00"), status=task_status("IN_PROGRESS"),
                           task_type=task_type("DEV"))
    bug_task = TaskFactory(estimated_hours=Decimal("6.00"), status=task_status("IN_PROGRESS"),
                           task_type=task_type("BUG_FIX"))
    TaskAssignment.objects.create(task=dev_task, employee=emp, legacy_code="ASG-911")
    TaskAssignment.objects.create(task=bug_task, employee=emp, legacy_code="ASG-912")

    row = _row(emp)
    assert row["assigned_hours"] == 10.0
    assert row["open_tasks"] == 2
