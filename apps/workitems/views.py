from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_TEAM
from apps.core.views import BaseModelViewSet

from .filters import WorkItemFilter, WorkItemMilestoneFilter, WorkItemTaskFilter
from .models import WorkItem, WorkItemMilestone, WorkItemMilestoneTask, WorkItemTask
from .serializers import (
    WorkItemDetailSerializer,
    WorkItemListSerializer,
    WorkItemMilestoneSerializer,
    WorkItemTaskDetailSerializer,
    WorkItemTaskListSerializer,
    WorkItemTaskWriteSerializer,
    WorkItemWriteSerializer,
)

# Any Team Member can log Continuous Improvement work, not just Admin/PM —
# it's meant to be self-serve, same write_roles as Task/SubTask.
CI_WRITE_ROLES = (ROLE_ADMIN, ROLE_PM, ROLE_TEAM)


class WorkItemViewSet(BaseModelViewSet):
    """CRUD for Continuous Improvement work items (docs, tech debt, proxy
    adjustments) — optionally traced to the delivered Project they touch."""

    legacy_prefix = "WKI"
    write_roles = CI_WRITE_ROLES
    filterset_class = WorkItemFilter
    search_fields = ["title", "description", "legacy_code"]
    ordering_fields = ["title", "created_at"]
    serializer_class = WorkItemDetailSerializer

    def get_queryset(self):
        return (
            WorkItem.active.select_related("project", "status", "priority")
            .annotate(task_count=Count("tasks", filter=Q(tasks__is_active=True)))
        )

    def get_serializer_class(self):
        return {
            "list": WorkItemListSerializer,
            "create": WorkItemWriteSerializer,
            "update": WorkItemWriteSerializer,
            "partial_update": WorkItemWriteSerializer,
        }.get(self.action, WorkItemDetailSerializer)


class WorkItemTaskViewSet(BaseModelViewSet):
    """Flat tasks under a WorkItem — no subtask nesting by design."""

    legacy_prefix = "WIT"
    write_roles = CI_WRITE_ROLES
    filterset_class = WorkItemTaskFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["planned_end", "priority", "created_at"]
    serializer_class = WorkItemTaskDetailSerializer

    def get_queryset(self):
        return (
            WorkItemTask.active
            .select_related("work_item", "assignee", "status", "priority")
        )

    def get_serializer_class(self):
        return {
            "list": WorkItemTaskListSerializer,
            "create": WorkItemTaskWriteSerializer,
            "update": WorkItemTaskWriteSerializer,
            "partial_update": WorkItemTaskWriteSerializer,
        }.get(self.action, WorkItemTaskDetailSerializer)


class WorkItemMilestoneViewSet(BaseModelViewSet):
    """CRUD for WorkItem milestones (e.g. "docs handed to team X"); status/
    progress derived from linked tasks, added manually — zero, one or several
    per WorkItem, same as Project's Milestone."""

    legacy_prefix = "WIM"
    write_roles = CI_WRITE_ROLES
    serializer_class = WorkItemMilestoneSerializer
    filterset_class = WorkItemMilestoneFilter
    search_fields = ["name", "legacy_code"]
    ordering_fields = ["target_date", "created_at"]

    def get_queryset(self):
        return WorkItemMilestone.active.select_related("work_item", "owner_employee").all()

    @action(detail=True, methods=["post"])
    def tasks(self, request, pk=None):
        """Link a WorkItemTask to this milestone. Body: ``{"task": "<uuid>"}``."""
        milestone = self.get_object()
        task = get_object_or_404(WorkItemTask, pk=request.data.get("task"))
        link, created = WorkItemMilestoneTask.objects.get_or_create(milestone=milestone, task=task)
        return Response({"created": created, "id": link.id},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
