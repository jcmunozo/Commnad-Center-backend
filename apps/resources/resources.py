from import_export import fields
from import_export.widgets import ForeignKeyWidget

from apps.catalogs.models import EmployeeLevel, EmployeeStatus, Location, Timezone
from apps.core.import_resources import SafeModelResource, catalog_field, employee_field
from apps.projects.models import Task

from .models import Employee, TaskAssignment


class EmployeeResource(SafeModelResource):
    # Manager is imported in a second pass (see imports.orchestrator): rows are
    # created first without it so references within the sheet resolve. Names
    # not present in the roster (external managers) import as null.
    manager = employee_field("manager")
    level = catalog_field("level", EmployeeLevel)
    status = catalog_field("status", EmployeeStatus)
    location = catalog_field("location", Location)
    timezone = catalog_field("timezone", Timezone)

    class Meta:
        model = Employee
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "name", "role", "manager", "availability_pct", "weekly_hours",
                  "level", "status", "location", "timezone")
        skip_unchanged = True
        clean_model_instances = True


class TaskAssignmentResource(SafeModelResource):
    task = fields.Field(column_name="task", attribute="task",
                        widget=ForeignKeyWidget(Task, field="legacy_code"))
    employee = fields.Field(column_name="employee", attribute="employee",
                            widget=ForeignKeyWidget(Employee, field="legacy_code"))

    class Meta:
        model = TaskAssignment
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "task", "employee", "assigned_date", "delivery_date")
        clean_model_instances = True
