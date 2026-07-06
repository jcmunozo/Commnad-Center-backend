from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_TEAM
from apps.core.views import BaseModelViewSet

from .filters import ActionFilter, IssueFilter, ProjectUpdateFilter, RiskFilter
from .models import Action, Issue, ProjectUpdate, Risk
from .serializers import (
    ActionSerializer,
    IssueSerializer,
    ProjectUpdateSerializer,
    RiskSerializer,
)


class IssueViewSet(BaseModelViewSet):
    write_roles = (ROLE_ADMIN, ROLE_PM, ROLE_TEAM)
    serializer_class = IssueSerializer
    filterset_class = IssueFilter
    search_fields = ["description", "legacy_code"]
    ordering_fields = ["date_reported", "created_at"]

    def get_queryset(self):
        return Issue.active.select_related("project", "status", "assignee").all()


class RiskViewSet(BaseModelViewSet):
    write_roles = (ROLE_ADMIN, ROLE_PM)
    serializer_class = RiskSerializer
    filterset_class = RiskFilter
    search_fields = ["description", "legacy_code"]
    ordering_fields = ["exposure", "created_at"]

    def get_queryset(self):
        return Risk.active.select_related("project", "status", "owner_employee").all()


class ProjectUpdateViewSet(BaseModelViewSet):
    write_roles = (ROLE_ADMIN, ROLE_PM, ROLE_TEAM)
    serializer_class = ProjectUpdateSerializer
    filterset_class = ProjectUpdateFilter
    search_fields = ["description", "legacy_code"]
    ordering_fields = ["update_date", "due_date"]

    def get_queryset(self):
        return ProjectUpdate.active.select_related("project", "update_type", "status").all()


class ActionViewSet(BaseModelViewSet):
    write_roles = (ROLE_ADMIN, ROLE_PM, ROLE_TEAM)
    serializer_class = ActionSerializer
    filterset_class = ActionFilter
    search_fields = ["description", "legacy_code"]
    ordering_fields = ["due_date", "priority", "created_date"]

    def get_queryset(self):
        return Action.active.select_related("project", "status", "assignee", "priority").all()
