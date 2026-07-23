from django.db.models import BooleanField, Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.views import BaseModelViewSet

from . import services
from .filters import (
    MilestoneFilter,
    ProjectFilter,
    SubTaskFilter,
    TaskFilter,
)
from .models import (
    Milestone,
    MilestoneTask,
    Project,
    ProjectFavorite,
    ProjectPhase,
    SubTask,
    Task,
)
from .serializers import (
    DashboardSerializer,
    MilestoneSerializer,
    ProgressSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectPhaseSerializer,
    ProjectWriteSerializer,
    SubTaskSerializer,
    TaskDependencySerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskWriteSerializer,
)


class ProjectViewSet(BaseModelViewSet):
    """CRUD + PMO analytics for projects."""

    legacy_prefix = "PRJ"
    filterset_class = ProjectFilter
    search_fields = ["name", "legacy_code", "trigger_name", "target_name"]
    ordering_fields = ["name", "planned_end", "progress_pct", "created_at", "is_favorite"]
    serializer_class = ProjectDetailSerializer

    def get_queryset(self):
        qs = Project.active.select_related("status", "priority", "health").all()
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return qs.annotate(is_favorite=Value(False, output_field=BooleanField()))
        return qs.annotate(is_favorite=Exists(
            ProjectFavorite.objects.filter(project=OuterRef("pk"), user=user)))

    @extend_schema(request=None, responses={200: {"type": "object",
                   "properties": {"is_favorite": {"type": "boolean"}}}})
    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        """Toggle the current user's star on this project (personal, per-user)."""
        project = self.get_object()
        fav, created = ProjectFavorite.objects.get_or_create(
            user=request.user, project=project)
        if not created:
            fav.delete()
        return Response({"is_favorite": created})

    def get_serializer_class(self):
        return {
            "list": ProjectListSerializer,
            "create": ProjectWriteSerializer,
            "update": ProjectWriteSerializer,
            "partial_update": ProjectWriteSerializer,
        }.get(self.action, ProjectDetailSerializer)

    @extend_schema(responses=DashboardSerializer)
    @action(detail=True, methods=["get"])
    def dashboard(self, request, pk=None):
        """Aggregated KPIs for the project (open/overdue tasks, issues, risks, endpoints)."""
        data = services.project_dashboard(self.get_object())
        return Response(DashboardSerializer(data).data)

    @extend_schema(responses=ProgressSerializer)
    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        """Hours-weighted progress across the project's active tasks."""
        data = services.weighted_progress(self.get_object())
        return Response(ProgressSerializer(data).data)

    PHASE_ORDER = [code for code, _ in ProjectPhase.PHASES]

    @extend_schema(request=ProjectPhaseSerializer(many=True),
                   responses=ProjectPhaseSerializer(many=True))
    @action(detail=True, methods=["get", "put"])
    def phases(self, request, pk=None):
        """Get or replace the project's phase timeline (Dev/SIT/UAT/Prod/Hypercare)."""
        project = self.get_object()
        if request.method == "PUT":
            serializer = ProjectPhaseSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            codes = [row["phase"] for row in serializer.validated_data]
            if len(codes) != len(set(codes)):
                return Response({"detail": "Duplicate phase codes in payload."},
                                status=status.HTTP_400_BAD_REQUEST)
            project.phases.all().delete()
            ProjectPhase.objects.bulk_create([
                ProjectPhase(project=project, **row) for row in serializer.validated_data
            ])
        qs = sorted(project.phases.all(), key=lambda p: self.PHASE_ORDER.index(p.phase))
        return Response(ProjectPhaseSerializer(qs, many=True).data)


class TaskViewSet(BaseModelViewSet):
    """CRUD for tasks + assignment/dependency sub-actions."""

    legacy_prefix = "TSK"
    write_roles = ("PMO Admin", "Project Manager", "Team Member")
    filterset_class = TaskFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["planned_end", "priority", "created_at"]
    serializer_class = TaskDetailSerializer

    def get_queryset(self):
        from django.db.models import Count, Prefetch, Q

        from apps.resources.models import TaskAssignment

        return (
            Task.active.select_related("project", "status", "priority", "task_type")
            .prefetch_related(Prefetch(
                "assignments",
                queryset=TaskAssignment.active.select_related("employee"),
                to_attr="active_assignments",
            ))
            .annotate(subtask_count=Count("subtasks", filter=Q(subtasks__is_active=True)))
        )

    def get_serializer_class(self):
        return {
            "list": TaskListSerializer,
            "create": TaskWriteSerializer,
            "update": TaskWriteSerializer,
            "partial_update": TaskWriteSerializer,
        }.get(self.action, TaskDetailSerializer)

    def _stamp_delivery(self, task):
        """A DONE task stamps the delivery date on its active assignments."""
        from django.utils import timezone

        if task.status_id == "DONE":
            task.assignments.filter(is_active=True, delivery_date__isnull=True).update(
                delivery_date=timezone.now())

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._stamp_delivery(serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._stamp_delivery(serializer.instance)

    @action(detail=True, methods=["get", "put"])
    def assignees(self, request, pk=None):
        """Get or replace the task's active assignees.

        PUT body: ``{"employees": ["<uuid>", ...]}``. Reactivates soft-deleted
        (task, employee) rows instead of recreating them — the DB unique
        constraint spans soft-deleted rows too.
        """
        from django.utils import timezone

        from apps.resources.models import Employee, TaskAssignment

        task = self.get_object()
        if request.method == "PUT":
            wanted = set(request.data.get("employees", []))
            if wanted and Employee.active.filter(id__in=wanted).count() != len(wanted):
                return Response({"detail": "Unknown or inactive employee id."},
                                status=status.HTTP_400_BAD_REQUEST)
            from apps.core.views import next_legacy_code

            delivery = timezone.now() if task.status_id == "DONE" else None
            existing = {str(a.employee_id): a for a in task.assignments.all()}
            for emp_id, a in existing.items():
                if emp_id in wanted and not a.is_active:
                    a.is_active = True
                    a.assigned_date = timezone.now()
                    a.delivery_date = a.delivery_date or delivery
                    a.save(update_fields=["is_active", "assigned_date", "delivery_date"])
                elif emp_id not in wanted and a.is_active:
                    a.soft_delete()
            for emp_id in wanted - existing.keys():
                TaskAssignment.objects.create(
                    task=task, employee_id=emp_id, assigned_date=timezone.now(),
                    delivery_date=delivery,
                    legacy_code=next_legacy_code(TaskAssignment, "ASG"))
        rows = task.assignments.filter(is_active=True).select_related("employee")
        return Response([{"id": str(a.employee_id), "name": a.employee.name} for a in rows])

    @action(detail=True, methods=["post"], serializer_class=TaskDependencySerializer)
    def dependencies(self, request, pk=None):
        """Add a 'blocked by' dependency to this task."""
        task = self.get_object()
        payload = {"task": task.id, "blocked_by": request.data.get("blocked_by")}
        serializer = TaskDependencySerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MilestoneViewSet(BaseModelViewSet):
    """CRUD for milestones; status/progress derived from linked tasks."""

    legacy_prefix = "MIL"
    serializer_class = MilestoneSerializer
    filterset_class = MilestoneFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["target_date", "created_at"]

    def get_queryset(self):
        return Milestone.active.select_related("project", "owner_employee").all()

    @action(detail=True, methods=["post"])
    def tasks(self, request, pk=None):
        """Link a task to this milestone. Body: ``{"task": "<uuid>"}``."""
        milestone = self.get_object()
        task = get_object_or_404(Task, pk=request.data.get("task"))
        link, created = MilestoneTask.objects.get_or_create(milestone=milestone, task=task)
        return Response({"created": created, "id": link.id},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SubTaskViewSet(BaseModelViewSet):
    """Subtasks hanging off a task (debt or reminders)."""

    legacy_prefix = "SUB"
    write_roles = ("PMO Admin", "Project Manager", "Team Member")
    serializer_class = SubTaskSerializer
    filterset_class = SubTaskFilter
    search_fields = ["description", "legacy_code"]
    ordering_fields = ["due_date", "created_at"]

    def get_queryset(self):
        return SubTask.active.select_related("task", "assignee", "status", "priority").all()
