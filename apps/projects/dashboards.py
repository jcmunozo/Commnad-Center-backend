"""Portfolio-wide dashboards (aggregate KPIs and alerts)."""
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_VIEWER, role_required
from .models import Milestone, Project, SubTask, Task
from .selectors import milestone_progress

CLOSED_TASK = ("DONE", "CANCELLED")


class PortfolioDashboardView(APIView):
    """Aggregated KPIs across the whole portfolio."""

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM, ROLE_VIEWER)]

    @extend_schema(responses=dict)
    def get(self, request):
        now = timezone.now()
        projects = Project.active.all()
        tasks = Task.active.all()
        open_tasks = tasks.exclude(status_id__in=CLOSED_TASK)
        data = {
            "total_projects": projects.count(),
            "active_projects": projects.exclude(status_id__in=("COMPLETED", "CANCELLED")).count(),
            "blocked_projects": projects.filter(status_id="BLOCKED").count(),
            "open_tasks": open_tasks.count(),
            "overdue_tasks": open_tasks.filter(planned_end__lt=now).count(),
            "overdue_subtasks": SubTask.active.filter(due_date__lt=now)
                                               .exclude(status_id__in=("COMPLETED", "CANCELLED"))
                                               .count(),
            "by_status": _count_by(projects, "status_id"),
            "by_task_status": _count_by(Task.active.all(), "status_id"),
            "projects": [
                {"id": str(p.id), "legacy_code": p.legacy_code, "name": p.name,
                 "progress_pct": float(p.progress_pct or 0), "health": p.health_id}
                for p in projects.order_by("-progress_pct")
            ],
        }
        return Response(data)


class AlertsView(APIView):
    """Schedule deviations: overdue subtasks and milestones."""

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM)]

    def get(self, request):
        now = timezone.now()
        overdue_subtasks = [
            {"id": str(s.id), "description": s.description, "due_date": s.due_date,
             "task_code": s.task.legacy_code, "task_name": s.task.name,
             "assignee_name": s.assignee.name if s.assignee else None,
             "project_id": str(s.task.project_id)}
            for s in SubTask.active.filter(due_date__lt=now)
            .exclude(status_id__in=("COMPLETED", "CANCELLED"))
            .select_related("task", "assignee")
        ]
        overdue_milestones = [
            {"id": str(m.id), "name": m.name, "target_date": m.target_date,
             **milestone_progress(m)}
            for m in Milestone.active.filter(target_date__lt=now)
            if milestone_progress(m)["derived_status"] != "COMPLETED"
        ]
        return Response({
            "overdue_subtasks": overdue_subtasks,
            "overdue_milestones": overdue_milestones,
        })


def _count_by(qs, field):
    from django.db.models import Count
    return {row[field]: row["n"] for row in qs.values(field).annotate(n=Count("id"))}
