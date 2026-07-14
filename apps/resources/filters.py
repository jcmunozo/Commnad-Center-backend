from django_filters import rest_framework as filters

from .models import Employee, TaskAssignment


class EmployeeFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Employee
        fields = ["level", "status", "location", "timezone", "manager", "is_active"]


class TaskAssignmentFilter(filters.FilterSet):
    project = filters.UUIDFilter(field_name="task__project")

    class Meta:
        model = TaskAssignment
        fields = ["task", "employee", "is_active"]
