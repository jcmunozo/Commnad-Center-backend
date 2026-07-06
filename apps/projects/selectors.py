"""Reusable read queries (thin views delegate here)."""
from django.db.models import Count, Q

from .models import Milestone, Task

CLOSED_TASK_STATUSES = ("DONE", "CANCELLED")


def open_task_qs(project_id):
    return Task.active.filter(project_id=project_id).exclude(status_id__in=CLOSED_TASK_STATUSES)


def milestone_progress(milestone: Milestone) -> dict:
    """Derive status/progress of a milestone from its tasks (Fase 1 #2)."""
    agg = milestone.tasks(manager="active").aggregate(
        total=Count("id"),
        done=Count("id", filter=Q(status_id="DONE")),
    )
    total, done = agg["total"] or 0, agg["done"] or 0
    tasks = milestone.tasks(manager="active").all()
    avg = sum((t.progress_pct for t in tasks), start=0) / total if total else 0
    if total == 0:
        status = "PENDING"
    elif done == total:
        status = "COMPLETED"
    else:
        status = "IN_PROGRESS"
    return {"total_tasks": total, "done_tasks": done, "avg_progress": round(float(avg), 4),
            "derived_status": status}
