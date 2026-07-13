from import_export import fields
from import_export.widgets import ForeignKeyWidget

from apps.catalogs.models import ActionOrigin, ActionStatus, IssueStatus, RiskStatus, SeverityLevel
from apps.core.import_resources import SafeModelResource, catalog_field, employee_field
from apps.projects.models import ApiComponent, Project

from .models import Action, Issue, Risk


def _project_field():
    return fields.Field(column_name="project", attribute="project",
                        widget=ForeignKeyWidget(Project, field="legacy_code"))


def _api_field():
    return fields.Field(column_name="api", attribute="api",
                        widget=ForeignKeyWidget(ApiComponent, field="legacy_code"))


class IssueResource(SafeModelResource):
    project = _project_field()
    api = _api_field()
    impact = catalog_field("impact", SeverityLevel)
    urgency = catalog_field("urgency", SeverityLevel)
    status = catalog_field("status", IssueStatus)
    assignee = employee_field("assignee")

    class Meta:
        model = Issue
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "date_reported", "reported_by_name",
                  "description", "impact", "urgency", "assignee", "status",
                  "resolution_date", "lessons_learned")
        clean_model_instances = True


class RiskResource(SafeModelResource):
    project = _project_field()
    status = catalog_field("status", RiskStatus)
    owner_employee = employee_field("owner_employee")

    class Meta:
        model = Risk
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "description", "probability", "impact",
                  "mitigation_plan", "owner_employee", "status", "identified_date", "last_review")
        clean_model_instances = True


class ActionResource(SafeModelResource):
    project = _project_field()
    api = _api_field()
    origin = catalog_field("origin", ActionOrigin)
    priority = catalog_field("priority", SeverityLevel)
    impact = catalog_field("impact", SeverityLevel)
    status = catalog_field("status", ActionStatus)
    assignee = employee_field("assignee")

    class Meta:
        model = Action
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "created_date", "origin", "description",
                  "assignee", "due_date", "priority", "impact", "status", "notes")
        clean_model_instances = True
