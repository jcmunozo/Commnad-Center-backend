"""Portfolio-wide dashboards (aggregate KPIs and alerts)."""
from datetime import timedelta

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_VIEWER, role_required
from .models import Milestone, Project, Sprint, SubTask, Task
from .selectors import milestone_progress, sprint_scope_q

CLOSED_TASK = ("DONE", "CANCELLED")


def _resolve_sprint(request):
    """None when ?sprint_id isn't passed (all-time, today's behavior);
    404s on a bad id via get_object_or_404."""
    sprint_id = request.query_params.get("sprint_id")
    if not sprint_id:
        return None
    return get_object_or_404(Sprint, pk=sprint_id)


class PortfolioDashboardView(APIView):
    """Aggregated KPIs across the whole portfolio, optionally scoped to one
    sprint via ``?sprint_id=``. Projects/by_status stay portfolio-wide
    regardless of the sprint filter — there is no Project<->Sprint relation,
    only Task<->Sprint."""

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM, ROLE_VIEWER)]

    @extend_schema(responses=dict)
    def get(self, request):
        now = timezone.now()
        sprint = _resolve_sprint(request)
        projects = Project.active.all()
        tasks = Task.active.all()
        if sprint is not None:
            tasks = tasks.filter(sprint_scope_q(sprint))
        open_tasks = tasks.exclude(status_id__in=CLOSED_TASK)

        overdue_subtasks_qs = SubTask.active.filter(due_date__lt=now).exclude(
            status_id__in=("COMPLETED", "CANCELLED"))
        if sprint is not None:
            # SubTask has no sprint of its own — scope via its parent Task.
            overdue_subtasks_qs = overdue_subtasks_qs.filter(task__in=tasks)

        data = {
            "total_projects": projects.count(),
            "active_projects": projects.exclude(status_id__in=("COMPLETED", "CANCELLED")).count(),
            "blocked_projects": projects.filter(status_id="BLOCKED").count(),
            "open_tasks": open_tasks.count(),
            "overdue_tasks": open_tasks.filter(planned_end__lt=now).count(),
            "overdue_subtasks": overdue_subtasks_qs.count(),
            "by_status": _count_by(projects, "status_id"),
            "by_task_status": _count_by(tasks, "status_id"),
            "projects": [
                {"id": str(p.id), "legacy_code": p.legacy_code, "name": p.name,
                 "progress_pct": float(p.progress_pct or 0), "health": p.health_id}
                for p in projects.order_by("-progress_pct")
            ],
            "tasks_effort": [
                {"id": str(t.id), "legacy_code": t.legacy_code, "name": t.name,
                 "project_name": t.project.name, "status": t.status_id,
                 "estimated_hours": float(t.estimated_hours),
                 "actual_hours": float(t.actual_hours) if t.actual_hours is not None else 0.0}
                for t in tasks.exclude(estimated_hours__isnull=True)
                               .select_related("project")
                               .order_by("project__legacy_code", "legacy_code")
            ],
        }
        if sprint is not None:
            data["sprint"] = {"id": str(sprint.id), "name": sprint.name}
            totals = tasks.exclude(estimated_hours__isnull=True).aggregate(
                estimated_hours=Sum("estimated_hours"), actual_hours=Sum("actual_hours"))
            data["sprint_effort_totals"] = {
                "estimated_hours": float(totals["estimated_hours"] or 0),
                "actual_hours": float(totals["actual_hours"] or 0),
            }
        return Response(data)


class AlertsView(APIView):
    """Schedule deviations: overdue subtasks and milestones, optionally
    scoped to one sprint via ``?sprint_id=``.

    Milestones have no direct Sprint relation (they're project-level), so
    "milestone belongs to sprint X" is a heuristic: at least one of its
    linked tasks (Milestone.tasks, via MilestoneTask) is in that sprint's
    scope. This is a weaker signal than the FK-based task/subtask scoping
    above — a milestone can show up for a sprint even if most of its tasks
    aren't in it, and vice versa.
    """

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM)]

    def get(self, request):
        now = timezone.now()
        sprint = _resolve_sprint(request)

        subtasks_qs = SubTask.active.filter(due_date__lt=now).exclude(
            status_id__in=("COMPLETED", "CANCELLED")).select_related("task", "assignee")
        milestones_qs = Milestone.active.filter(target_date__lt=now)
        if sprint is not None:
            scoped_tasks = Task.active.filter(sprint_scope_q(sprint))
            subtasks_qs = subtasks_qs.filter(task__in=scoped_tasks)
            milestones_qs = milestones_qs.filter(tasks__in=scoped_tasks).distinct()

        overdue_subtasks = [
            {"id": str(s.id), "description": s.description, "due_date": s.due_date,
             "task_code": s.task.legacy_code, "task_name": s.task.name,
             "assignee_name": s.assignee.name if s.assignee else None,
             "project_id": str(s.task.project_id)}
            for s in subtasks_qs
        ]
        overdue_milestones = [
            {"id": str(m.id), "name": m.name, "target_date": m.target_date,
             **milestone_progress(m)}
            for m in milestones_qs
            if milestone_progress(m)["derived_status"] != "COMPLETED"
        ]
        return Response({
            "overdue_subtasks": overdue_subtasks,
            "overdue_milestones": overdue_milestones,
        })


class BurndownView(APIView):
    """Remaining estimated hours vs. an idealized straight-line burn, for
    one sprint (``?sprint_id=`` required).

    ``total_scope_hours`` is a live snapshot of whatever is currently
    ``sprint_scope_q()``-linked to the sprint, not a scope frozen at sprint
    start — tasks added or removed mid-sprint change it retroactively. The
    frontend shows a caption about this; see the sprint-dashboard plan.
    """

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM, ROLE_VIEWER)]

    def get(self, request):
        sprint_id = request.query_params.get("sprint_id")
        if not sprint_id:
            return Response({"detail": "sprint_id is required."}, status=400)
        sprint = get_object_or_404(Sprint, pk=sprint_id)

        sprint_payload = {
            "id": str(sprint.id), "name": sprint.name,
            "start_date": sprint.start_date.isoformat(), "end_date": sprint.end_date.isoformat(),
        }
        tasks = list(
            Task.active.filter(sprint_scope_q(sprint))
            .exclude(estimated_hours__isnull=True)
            .values("estimated_hours", "completed_at")
        )
        total_scope_hours = float(sum(t["estimated_hours"] for t in tasks))
        if not tasks or total_scope_hours == 0:
            return Response({"sprint": sprint_payload, "total_scope_hours": 0.0, "days": []})

        today = timezone.localdate()
        last_day = min(sprint.end_date, today)
        total_days = (sprint.end_date - sprint.start_date).days

        days = []
        day = sprint.start_date
        while day <= last_day:
            completed_hours = sum(
                float(t["estimated_hours"]) for t in tasks
                if t["completed_at"] is not None and t["completed_at"].date() <= day
            )
            elapsed = (day - sprint.start_date).days
            ideal_hours = total_scope_hours * (1 - elapsed / total_days) if total_days > 0 else 0.0
            days.append({
                "date": day.isoformat(),
                "remaining_hours": round(total_scope_hours - completed_hours, 2),
                "ideal_hours": round(max(ideal_hours, 0.0), 2),
            })
            day += timedelta(days=1)

        return Response({
            "sprint": sprint_payload,
            "total_scope_hours": round(total_scope_hours, 2),
            "days": days,
        })


class VelocityView(APIView):
    """Tasks/hours completed per sprint, trended across the last N *closed*
    sprints (``?limit=``, default 6). Independent of any single sprint
    selection — always strict ``sprint_id`` + ``status_id="DONE"`` match,
    which is unambiguous for a closed sprint (no carry-over case to
    consider, unlike ``sprint_scope_q()`` for the active sprint)."""

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM, ROLE_VIEWER)]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 6))
        except ValueError:
            limit = 6
        limit = max(1, min(limit, 24))

        closed_sprints = list(
            Sprint.active.filter(status=Sprint.STATUS_CLOSED).order_by("-start_date")[:limit])
        closed_sprints.reverse()

        sprints_payload = []
        for sprint in closed_sprints:
            done_tasks = Task.active.filter(sprint_id=sprint.id, status_id="DONE")
            totals = done_tasks.aggregate(
                tasks_done=Count("id"),
                estimated_hours=Sum("estimated_hours"),
                actual_hours=Sum("actual_hours"),
            )
            estimated_hours = float(totals["estimated_hours"] or 0)
            sprints_payload.append({
                "id": str(sprint.id), "name": sprint.name,
                "start_date": sprint.start_date.isoformat(), "end_date": sprint.end_date.isoformat(),
                "tasks_done": totals["tasks_done"] or 0,
                "hours_done": estimated_hours,
                "estimated_hours": estimated_hours,
                "actual_hours": float(totals["actual_hours"] or 0),
            })
        return Response({"sprints": sprints_payload})


def _count_by(qs, field):
    return {row[field]: row["n"] for row in qs.values(field).annotate(n=Count("id"))}
