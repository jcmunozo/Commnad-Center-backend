from django_filters import rest_framework as filters

from .models import Action, Issue, ProjectUpdate, Risk


class IssueFilter(filters.FilterSet):
    class Meta:
        model = Issue
        fields = ["project", "api", "status", "assignee", "impact", "urgency", "is_active"]


class RiskFilter(filters.FilterSet):
    min_exposure = filters.NumberFilter(field_name="exposure", lookup_expr="gte")

    class Meta:
        model = Risk
        fields = ["project", "status", "owner_employee", "is_active"]


class ProjectUpdateFilter(filters.FilterSet):
    class Meta:
        model = ProjectUpdate
        fields = ["project", "api", "update_type", "status", "responsible", "is_active"]


class ActionFilter(filters.FilterSet):
    due_before = filters.DateTimeFilter(field_name="due_date", lookup_expr="lte")
    due_after = filters.DateTimeFilter(field_name="due_date", lookup_expr="gte")

    class Meta:
        model = Action
        fields = ["project", "api", "status", "assignee", "priority", "origin", "is_active"]
