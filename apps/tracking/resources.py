from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from apps.projects.models import Project

from .models import Action, Issue, Risk


def _project_field():
    return fields.Field(column_name="project", attribute="project",
                        widget=ForeignKeyWidget(Project, field="legacy_code"))


class IssueResource(resources.ModelResource):
    project = _project_field()

    class Meta:
        model = Issue
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "date_reported", "reported_by_name",
                  "description", "impact", "urgency", "status", "resolution_date", "lessons_learned")


class RiskResource(resources.ModelResource):
    project = _project_field()

    class Meta:
        model = Risk
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "description", "probability", "impact",
                  "mitigation_plan", "status", "identified_date", "last_review")


class ActionResource(resources.ModelResource):
    project = _project_field()

    class Meta:
        model = Action
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "project", "api", "created_date", "origin", "description",
                  "due_date", "priority", "impact", "status", "notes")
