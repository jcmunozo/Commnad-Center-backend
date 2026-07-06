"""Portfolio-wide dashboards (aggregate KPIs and alerts)."""
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_VIEWER, role_required
from apps.tracking.models import Action, Risk

from .models import Milestone, Project, Task
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
            "critical_risks": Risk.active.filter(probability__gte=4, impact__gte=4)
                                          .exclude(status_id="CLOSED").count(),
            "by_status": _count_by(projects, "status_id"),
        }
        return Response(data)


class AlertsView(APIView):
    """Critical risks and schedule deviations (overdue milestones/actions)."""

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM)]

    def get(self, request):
        now = timezone.now()
        critical_risks = list(
            Risk.active.filter(probability__gte=4, impact__gte=4).exclude(status_id="CLOSED")
            .values("id", "project_id", "description", "probability", "impact")
        )
        overdue_actions = list(
            Action.active.filter(due_date__lt=now).exclude(status_id__in=("COMPLETED", "CANCELLED"))
            .values("id", "project_id", "description", "due_date")
        )
        overdue_milestones = [
            {"id": str(m.id), "name": m.name, "target_date": m.target_date,
             **milestone_progress(m)}
            for m in Milestone.active.filter(target_date__lt=now)
            if milestone_progress(m)["derived_status"] != "COMPLETED"
        ]
        return Response({
            "critical_risks": critical_risks,
            "overdue_actions": overdue_actions,
            "overdue_milestones": overdue_milestones,
        })


def _count_by(qs, field):
    from django.db.models import Count
    return {row[field]: row["n"] for row in qs.values(field).annotate(n=Count("id"))}
