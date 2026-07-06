from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from . import resources
from .models import ApiComponent, Endpoint, Milestone, Project, Task


@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    resource_class = resources.ProjectResource
    list_display = ("legacy_code", "name", "client", "status", "priority", "progress_pct")
    list_filter = ("status", "priority", "project_type")
    search_fields = ("name", "legacy_code")


@admin.register(ApiComponent)
class ApiComponentAdmin(ImportExportModelAdmin):
    resource_class = resources.ApiComponentResource
    list_display = ("legacy_code", "name", "owner_project", "status")


@admin.register(Endpoint)
class EndpointAdmin(ImportExportModelAdmin):
    resource_class = resources.EndpointResource
    list_display = ("legacy_code", "http_method", "path", "api", "status")


@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):
    resource_class = resources.TaskResource
    list_display = ("legacy_code", "name", "project", "status", "priority")
    list_filter = ("status", "priority", "task_type")


@admin.register(Milestone)
class MilestoneAdmin(ImportExportModelAdmin):
    resource_class = resources.MilestoneResource
    list_display = ("legacy_code", "name", "project", "target_date")
