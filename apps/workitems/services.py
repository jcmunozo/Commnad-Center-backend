"""Continuous Improvement hours, independent of formal project delivery.

Unlike apps.tickets (hours derived from a WIP status log), WorkItemTask hours
are manual — ``estimated_hours`` is authoritative, same as apps.projects.Task
(Fase 1 #10). This module must not import from apps.resources
(resources.services imports from here, same discipline as apps.tickets.services).
"""
from .models import WorkItemTask

ACTIVE_EXCLUDE = ("DONE", "CANCELLED")


def employee_workitem_hours(period_start=None, period_end=None) -> dict[str, dict]:
    """Per employee: estimated hours of their active WorkItemTasks, optionally
    windowed by the task's planned_start/planned_end (same convention as
    apps.projects.Task in employee_workload). Shape mirrors
    apps.tickets.services.employee_ticket_hours so resources.services can sum
    both the same way.
    """
    qs = WorkItemTask.active.filter(assignee__isnull=False).exclude(status_id__in=ACTIVE_EXCLUDE)
    if period_start:
        qs = qs.filter(planned_end__gte=period_start)
    if period_end:
        qs = qs.filter(planned_start__lte=period_end)

    data: dict[str, dict] = {}
    for t in qs.select_related("assignee"):
        row = data.setdefault(str(t.assignee_id), {"workitem_hours": 0.0, "open_workitem_tasks": 0})
        row["workitem_hours"] += float(t.estimated_hours or 0)
        row["open_workitem_tasks"] += 1
    for row in data.values():
        row["workitem_hours"] = round(row["workitem_hours"], 2)
    return data
