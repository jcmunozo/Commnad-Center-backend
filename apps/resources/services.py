"""Workload computation: task hours prorated across collaborators (Fase 2)."""
from decimal import Decimal

from django.db.models import Count

from apps.projects.models import Task

from .models import Employee, TaskAssignment

ACTIVE_TASK_EXCLUDE = ("DONE", "CANCELLED")


def employee_workload(period_start=None, period_end=None) -> list[dict]:
    """Return prorated assigned hours, capacity and workload % per active employee.

    Each active task's ``estimated_hours`` is split equally among its active
    assignees; every employee accumulates their share over active tasks.
    Optional ``period_*`` filters by the task's planned window.
    """
    task_qs = Task.active.exclude(status_id__in=ACTIVE_TASK_EXCLUDE)
    if period_start:
        task_qs = task_qs.filter(planned_end__gte=period_start)
    if period_end:
        task_qs = task_qs.filter(planned_start__lte=period_end)

    # collaborators per task
    counts = {
        row["task"]: row["n"]
        for row in TaskAssignment.active.filter(task__in=task_qs)
        .values("task").annotate(n=Count("id"))
    }

    shares: dict[str, Decimal] = {}
    assignments = (
        TaskAssignment.active.filter(task__in=task_qs)
        .select_related("task", "employee")
    )
    for a in assignments:
        n = counts.get(a.task_id, 1) or 1
        est = a.task.estimated_hours or Decimal(0)
        shares[a.employee_id] = shares.get(a.employee_id, Decimal(0)) + est / n

    results = []
    for emp in Employee.active.all():
        assigned = shares.get(emp.id, Decimal(0))
        capacity = emp.capacity_hours or Decimal(0)
        workload = float(assigned / capacity) if capacity else 0.0
        results.append({
            "employee_id": str(emp.id),
            "name": emp.name,
            "assigned_hours": round(float(assigned), 2),
            "capacity_hours": round(float(capacity), 2),
            "workload_pct": round(workload, 4),
            "alert": _alert(workload),
        })
    return results


def _alert(workload: float) -> str:
    if workload > 1.0:
        return "OVERLOADED"
    if workload > 0.85:
        return "HIGH_LOAD"
    return "OK"
