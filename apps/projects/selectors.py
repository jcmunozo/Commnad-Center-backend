"""Reusable read queries (thin views delegate here)."""
from django.db.models import Count, Q

from .models import Milestone, Task

CLOSED_TASK_STATUSES = ("DONE", "CANCELLED")


def open_task_qs(project_id):
    return Task.active.filter(project_id=project_id).exclude(status_id__in=CLOSED_TASK_STATUSES)


def current_sprint_q(closed_statuses=CLOSED_TASK_STATUSES) -> Q:
    """Q for 'belongs to the current sprint', for any model with a `sprint`
    FK + a `status` FK sharing the same closed-status codes (Task, WorkItemTask).

    A row's `sprint` FK is never reassigned on ``start_next`` — it always
    points at the sprint it was originally created/assigned in. So "current
    sprint" membership is a read-time effect: the active sprint's own rows,
    plus any still-open row left pointing at an older, now-closed sprint. A
    row only drops out once it's actually DONE/CANCELLED, regardless of which
    sprint its FK still names.
    """
    from .models import Sprint

    active = Sprint.active.filter(status=Sprint.STATUS_ACTIVE).first()
    if active is None:
        return Q(pk__in=[])
    return Q(sprint_id=active.id) | (Q(sprint__isnull=False) & ~Q(status_id__in=closed_statuses))


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
