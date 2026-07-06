"""Business logic for project KPIs and weighted progress (fat services)."""
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.tracking.models import Issue, Risk

from .models import Endpoint, Task

CLOSED_TASK = ("DONE", "CANCELLED")


def project_dashboard(project) -> dict:
    """Aggregate KPIs for a single project (replaces the Excel COUNTIFS rollups)."""
    now = timezone.now()
    tasks = Task.active.filter(project=project)
    open_tasks = tasks.exclude(status_id__in=CLOSED_TASK)

    endpoints = Endpoint.active.filter(api__owner_project=project)
    issues = Issue.active.filter(project=project).exclude(status_id__in=("RESOLVED", "CLOSED"))
    risks = Risk.active.filter(project=project).exclude(status_id="CLOSED")

    return {
        "project_id": str(project.id),
        "open_tasks": open_tasks.count(),
        "overdue_tasks": open_tasks.filter(planned_end__lt=now).count(),
        "open_issues": issues.count(),
        "open_risks": risks.count(),
        "critical_risks": risks.filter(probability__gte=4, impact__gte=4).count(),
        "total_apis": project.owned_apis(manager="active").count(),
        "endpoints_total": endpoints.count(),
        "endpoints_done": endpoints.filter(status_id="DONE").count(),
    }


def weighted_progress(project) -> dict:
    """Progress weighted by estimated hours across active tasks.

    Falls back to a simple average of ``progress_pct`` when no task carries
    estimated hours. Effort lives on the task (Fase 1 #10).
    """
    tasks = Task.active.filter(project=project).exclude(status_id="CANCELLED")
    agg = tasks.aggregate(
        total_est=Coalesce(Sum("estimated_hours"), Decimal(0)),
        weighted=Coalesce(
            Sum(F("estimated_hours") * F("progress_pct"),
                output_field=DecimalField(max_digits=18, decimal_places=6)),
            Decimal(0),
        ),
        n=Count("id"),
        simple=Coalesce(
            Sum("progress_pct", output_field=DecimalField(max_digits=18, decimal_places=6)),
            Decimal(0),
        ),
    )
    if agg["total_est"] and agg["total_est"] > 0:
        pct = agg["weighted"] / agg["total_est"]
    elif agg["n"]:
        pct = agg["simple"] / agg["n"]
    else:
        pct = Decimal(0)
    return {"project_id": str(project.id), "weighted_progress_pct": round(float(pct), 4),
            "task_count": agg["n"]}
