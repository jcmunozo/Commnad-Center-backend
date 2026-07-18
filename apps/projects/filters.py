from django_filters import rest_framework as filters

from .models import Milestone, Project, SubTask, Task


class ProjectFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    planned_end_before = filters.DateTimeFilter(field_name="planned_end", lookup_expr="lte")
    planned_end_after = filters.DateTimeFilter(field_name="planned_end", lookup_expr="gte")
    # filters on the per-user is_favorite annotation added in the viewset
    favorite = filters.BooleanFilter(field_name="is_favorite")

    class Meta:
        model = Project
        fields = ["status", "priority", "health", "project_type", "is_active"]


class TaskFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    assignee = filters.UUIDFilter(field_name="assignees", distinct=True)
    planned_end_before = filters.DateTimeFilter(field_name="planned_end", lookup_expr="lte")
    planned_end_after = filters.DateTimeFilter(field_name="planned_end", lookup_expr="gte")
    overdue = filters.BooleanFilter(method="filter_overdue")

    class Meta:
        model = Task
        fields = ["project", "status", "priority", "task_type", "is_active"]

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(planned_end__lt=timezone.now()).exclude(
                status_id__in=("DONE", "CANCELLED"))
        return queryset


class MilestoneFilter(filters.FilterSet):
    target_before = filters.DateTimeFilter(field_name="target_date", lookup_expr="lte")
    target_after = filters.DateTimeFilter(field_name="target_date", lookup_expr="gte")

    class Meta:
        model = Milestone
        fields = ["project", "owner_employee", "is_active"]


class SubTaskFilter(filters.FilterSet):
    project = filters.UUIDFilter(field_name="task__project")
    due_before = filters.DateTimeFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = SubTask
        fields = ["task", "status", "assignee", "priority", "is_active"]
