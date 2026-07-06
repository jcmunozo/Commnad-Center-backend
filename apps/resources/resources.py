from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from apps.projects.models import Task

from .models import Employee, TaskAssignment


class EmployeeResource(resources.ModelResource):
    manager = fields.Field(column_name="manager", attribute="manager",
                           widget=ForeignKeyWidget(Employee, field="name"))

    class Meta:
        model = Employee
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "name", "role", "manager", "availability_pct", "weekly_hours",
                  "level", "status", "location", "timezone")
        skip_unchanged = True


class TaskAssignmentResource(resources.ModelResource):
    task = fields.Field(column_name="task", attribute="task",
                        widget=ForeignKeyWidget(Task, field="legacy_code"))
    employee = fields.Field(column_name="employee", attribute="employee",
                            widget=ForeignKeyWidget(Employee, field="legacy_code"))

    class Meta:
        model = TaskAssignment
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "task", "employee", "assigned_date", "delivery_date")
