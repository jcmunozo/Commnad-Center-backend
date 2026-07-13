from django_filters import rest_framework as filters

from .models import ApiComponent, Endpoint, Milestone, Project, Task


class ProjectFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    planned_end_before = filters.DateTimeFilter(field_name="planned_end", lookup_expr="lte")
    planned_end_after = filters.DateTimeFilter(field_name="planned_end", lookup_expr="gte")

    class Meta:
        model = Project
        fields = ["status", "priority", "health", "client", "project_type", "is_active"]


class TaskFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    assignee = filters.UUIDFilter(field_name="assignees", distinct=True)
    planned_end_before = filters.DateTimeFilter(field_name="planned_end", lookup_expr="lte")
    planned_end_after = filters.DateTimeFilter(field_name="planned_end", lookup_expr="gte")
    overdue = filters.BooleanFilter(method="filter_overdue")

    class Meta:
        model = Task
        fields = ["project", "status", "priority", "task_type", "api", "endpoint", "is_active"]

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(planned_end__lt=timezone.now()).exclude(
                status_id__in=("DONE", "CANCELLED"))
        return queryset


class ApiComponentFilter(filters.FilterSet):
    class Meta:
        model = ApiComponent
        fields = ["owner_project", "status", "is_active"]


class EndpointFilter(filters.FilterSet):
    class Meta:
        model = Endpoint
        fields = ["api", "http_method", "status", "is_active"]


class MilestoneFilter(filters.FilterSet):
    target_before = filters.DateTimeFilter(field_name="target_date", lookup_expr="lte")
    target_after = filters.DateTimeFilter(field_name="target_date", lookup_expr="gte")

    class Meta:
        model = Milestone
        fields = ["project", "api", "owner_employee", "is_active"]
