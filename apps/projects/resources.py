"""django-import-export resources for the projects app.

Each uses ``legacy_code`` (PRJ-001, TSK-001…) as the stable import key.
Cross-entity FKs resolve by the counterpart's legacy_code; catalog FKs resolve
by the catalog's display ``name`` (the workbook stores display values, e.g.
"In Progress"), and people by Employee.name.
"""
from import_export import fields
from import_export.widgets import ForeignKeyWidget

from apps.catalogs.models import (
    ApiStatus,
    EndpointStatus,
    HealthStatus,
    ProjectStatus,
    SeverityLevel,
    TaskStatus,
    TaskType,
)
from apps.clients.models import Client
from apps.core.import_resources import SafeModelResource, catalog_field, employee_field

from .models import ApiComponent, Endpoint, Milestone, Project, Task


class ProjectResource(SafeModelResource):
    client = fields.Field(
        column_name="client",
        attribute="client",
        widget=ForeignKeyWidget(Client, field="name"),
    )
    status = catalog_field("status", ProjectStatus)
    priority = catalog_field("priority", SeverityLevel)
    health = catalog_field("health", HealthStatus)

    class Meta:
        model = Project
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "name", "client", "project_type", "status", "priority",
                  "health", "start_date", "planned_end", "actual_end", "progress_pct",
                  "planned_hours", "consumed_hours", "comments")
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        # The workbook has no project-type column; default to the API catalog code.
        if not row.get("project_type"):
            row["project_type"] = "API"


class ApiComponentResource(SafeModelResource):
    owner_project = fields.Field(
        column_name="owner_project", attribute="owner_project",
        widget=ForeignKeyWidget(Project, field="legacy_code"))
    status = catalog_field("status", ApiStatus)
    owner_employee = employee_field("owner_employee")

    class Meta:
        model = ApiComponent
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "owner_project", "name", "description", "version",
                  "status", "owner_employee", "comments")
        clean_model_instances = True


class EndpointResource(SafeModelResource):
    api = fields.Field(column_name="api", attribute="api",
                       widget=ForeignKeyWidget(ApiComponent, field="legacy_code"))
    status = catalog_field("status", EndpointStatus)
    owner_employee = employee_field("owner_employee")

    class Meta:
        model = Endpoint
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "api", "http_method", "path", "description", "status",
                  "owner_employee", "comments")
        clean_model_instances = True


class TaskResource(SafeModelResource):
    project = fields.Field(column_name="project", attribute="project",
                           widget=ForeignKeyWidget(Project, field="legacy_code"))
    api = fields.Field(column_name="api", attribute="api",
                       widget=ForeignKeyWidget(ApiComponent, field="legacy_code"))
    endpoint = fields.Field(column_name="endpoint", attribute="endpoint",
                            widget=ForeignKeyWidget(Endpoint, field="legacy_code"))
    task_type = catalog_field("task_type", TaskType)
    status = catalog_field("status", TaskStatus)
    priority = catalog_field("priority", SeverityLevel)

    class Meta:
        model = Task
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "endpoint", "task_type", "name", "status",
                  "priority", "planned_start", "planned_end", "estimated_hours", "actual_hours",
                  "progress_pct", "notes")
        clean_model_instances = True


class MilestoneResource(SafeModelResource):
    project = fields.Field(column_name="project", attribute="project",
                           widget=ForeignKeyWidget(Project, field="legacy_code"))
    api = fields.Field(column_name="api", attribute="api",
                       widget=ForeignKeyWidget(ApiComponent, field="legacy_code"))
    owner_employee = employee_field("owner_employee")

    class Meta:
        model = Milestone
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "name", "owner_employee",
                  "target_date", "actual_date", "comments")
        clean_model_instances = True
