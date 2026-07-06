from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.views import BaseModelViewSet

from . import services
from .filters import (
    ApiComponentFilter,
    EndpointFilter,
    MilestoneFilter,
    ProjectFilter,
    TaskFilter,
)
from .models import ApiComponent, Endpoint, Milestone, MilestoneTask, Project, ProjectApiRef, Task
from .serializers import (
    ApiComponentSerializer,
    DashboardSerializer,
    EndpointSerializer,
    MilestoneSerializer,
    ProgressSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectWriteSerializer,
    TaskDependencySerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskWriteSerializer,
)


class ProjectViewSet(BaseModelViewSet):
    """CRUD + PMO analytics for projects."""

    filterset_class = ProjectFilter
    search_fields = ["name", "legacy_code", "client__name"]
    ordering_fields = ["name", "planned_end", "progress_pct", "created_at"]
    serializer_class = ProjectDetailSerializer

    def get_queryset(self):
        return Project.active.select_related("client", "status", "priority", "health").all()

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


class ApiComponentViewSet(BaseModelViewSet):
    """CRUD for reusable API components + reuse references."""

    serializer_class = ApiComponentSerializer
    filterset_class = ApiComponentFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return ApiComponent.active.select_related("owner_project", "status").all()

    @action(detail=True, methods=["post"])
    def reference(self, request, pk=None):
        """Reference this API from another project (reuse, Fase 2 #11).

        Body: ``{"project": "<uuid>", "note": "..."}``.
        """
        api = self.get_object()
        project_id = request.data.get("project")
        ref, created = ProjectApiRef.objects.get_or_create(
            api=api, project_id=project_id, defaults={"note": request.data.get("note", "")})
        return Response({"created": created, "id": ref.id},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class EndpointViewSet(BaseModelViewSet):
    write_roles = ("PMO Admin", "Project Manager", "Team Member")
    serializer_class = EndpointSerializer
    filterset_class = EndpointFilter
    search_fields = ["path", "legacy_code"]
    ordering_fields = ["path", "created_at"]

    def get_queryset(self):
        return Endpoint.active.select_related("api", "http_method", "status").all()


class TaskViewSet(BaseModelViewSet):
    """CRUD for tasks + assignment/dependency sub-actions."""

    write_roles = ("PMO Admin", "Project Manager", "Team Member")
    filterset_class = TaskFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["planned_end", "priority", "created_at"]
    serializer_class = TaskDetailSerializer

    def get_queryset(self):
        return Task.active.select_related("project", "status", "priority", "task_type").all()

    def get_serializer_class(self):
        return {
            "list": TaskListSerializer,
            "create": TaskWriteSerializer,
            "update": TaskWriteSerializer,
            "partial_update": TaskWriteSerializer,
        }.get(self.action, TaskDetailSerializer)

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

    serializer_class = MilestoneSerializer
    filterset_class = MilestoneFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["target_date", "created_at"]

    def get_queryset(self):
        return Milestone.active.select_related("project", "api", "owner_employee").all()

    @action(detail=True, methods=["post"])
    def tasks(self, request, pk=None):
        """Link a task to this milestone. Body: ``{"task": "<uuid>"}``."""
        milestone = self.get_object()
        task = get_object_or_404(Task, pk=request.data.get("task"))
        link, created = MilestoneTask.objects.get_or_create(milestone=milestone, task=task)
        return Response({"created": created, "id": link.id},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
