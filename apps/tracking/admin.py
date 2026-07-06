from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from . import resources
from .models import Action, Issue, ProjectUpdate, Risk


@admin.register(Issue)
class IssueAdmin(ImportExportModelAdmin):
    resource_class = resources.IssueResource
    list_display = ("legacy_code", "project", "status", "impact", "urgency", "assignee")
    list_filter = ("status", "impact", "urgency")


@admin.register(Risk)
class RiskAdmin(ImportExportModelAdmin):
    resource_class = resources.RiskResource
    list_display = ("legacy_code", "project", "probability", "impact", "exposure", "status")
    list_filter = ("status",)


@admin.register(Action)
class ActionAdmin(ImportExportModelAdmin):
    resource_class = resources.ActionResource
    list_display = ("legacy_code", "project", "status", "priority", "due_date", "assignee")
    list_filter = ("status", "priority", "origin")


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "project", "update_type", "status", "due_date")
    list_filter = ("update_type", "status")
