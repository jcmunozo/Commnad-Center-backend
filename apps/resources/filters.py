from django_filters import rest_framework as filters

from .models import Employee, Holiday, Leave, TaskAssignment


class EmployeeFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Employee
        fields = ["level", "status", "location", "timezone", "manager", "is_active"]


class LeaveFilter(filters.FilterSet):
    # date_from/date_to select leaves whose window overlaps the given range
    date_from = filters.DateFilter(field_name="end_date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="start_date", lookup_expr="lte")

    class Meta:
        model = Leave
        fields = ["employee", "leave_type", "is_active"]


class HolidayFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Holiday
        fields = ["location", "is_active"]


class TaskAssignmentFilter(filters.FilterSet):
    project = filters.UUIDFilter(field_name="task__project")

    class Meta:
        model = TaskAssignment
        fields = ["task", "employee", "is_active"]
