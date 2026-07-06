"""django-import-export resources for the projects app.

Each uses ``legacy_code`` (PRJ-001, TSK-001…) as the stable import key and
resolves FKs by the counterpart's legacy_code via ForeignKeyWidget.
"""
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from apps.clients.models import Client

from .models import ApiComponent, Endpoint, Milestone, Project, Task


class ProjectResource(resources.ModelResource):
    client = fields.Field(
        column_name="client",
        attribute="client",
        widget=ForeignKeyWidget(Client, field="name"),
    )

    class Meta:
        model = Project
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "name", "client", "project_type", "status", "priority",
                  "health", "start_date", "planned_end", "actual_end", "progress_pct",
                  "planned_hours", "consumed_hours", "comments")
        skip_unchanged = True
        report_skipped = True


class ApiComponentResource(resources.ModelResource):
    owner_project = fields.Field(
        column_name="owner_project", attribute="owner_project",
        widget=ForeignKeyWidget(Project, field="legacy_code"))

    class Meta:
        model = ApiComponent
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "owner_project", "name", "description", "version",
                  "status", "comments")


class EndpointResource(resources.ModelResource):
    api = fields.Field(column_name="api", attribute="api",
                       widget=ForeignKeyWidget(ApiComponent, field="legacy_code"))

    class Meta:
        model = Endpoint
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "api", "http_method", "path", "description", "status", "comments")


class TaskResource(resources.ModelResource):
    project = fields.Field(column_name="project", attribute="project",
                           widget=ForeignKeyWidget(Project, field="legacy_code"))
    api = fields.Field(column_name="api", attribute="api",
                       widget=ForeignKeyWidget(ApiComponent, field="legacy_code"))
    endpoint = fields.Field(column_name="endpoint", attribute="endpoint",
                            widget=ForeignKeyWidget(Endpoint, field="legacy_code"))

    class Meta:
        model = Task
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "endpoint", "task_type", "name", "status",
                  "priority", "planned_start", "planned_end", "estimated_hours", "actual_hours",
                  "progress_pct", "notes")


class MilestoneResource(resources.ModelResource):
    project = fields.Field(column_name="project", attribute="project",
                           widget=ForeignKeyWidget(Project, field="legacy_code"))

    class Meta:
        model = Milestone
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "name", "target_date", "actual_date", "comments")
