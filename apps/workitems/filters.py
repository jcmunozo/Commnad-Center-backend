from django.utils import timezone
from django_filters import rest_framework as filters

from .models import WorkItem, WorkItemMilestone, WorkItemTask


class WorkItemFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = WorkItem
        fields = ["project", "status", "priority", "is_active"]


class WorkItemTaskFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    overdue = filters.BooleanFilter(method="filter_overdue")
    # Find CI tasks by the delivered project they trace back to, without the
    # caller needing to know which WorkItem(s) they live under.
    project = filters.UUIDFilter(field_name="work_item__project")

    class Meta:
        model = WorkItemTask
        fields = ["work_item", "status", "priority", "assignee", "is_active"]

    def filter_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(planned_end__lt=timezone.now()).exclude(
                status_id__in=("DONE", "CANCELLED"))
        return queryset


class WorkItemMilestoneFilter(filters.FilterSet):
    target_before = filters.DateTimeFilter(field_name="target_date", lookup_expr="lte")
    target_after = filters.DateTimeFilter(field_name="target_date", lookup_expr="gte")

    class Meta:
        model = WorkItemMilestone
        fields = ["work_item", "owner_employee", "is_active"]
