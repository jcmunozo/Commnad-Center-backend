from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Milestone, Project, Sprint, SubTask, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "trigger_name", "target_name", "status",
                    "priority", "progress_pct")
    list_filter = ("status", "priority", "project_type")
    search_fields = ("name", "legacy_code")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "project", "status", "priority", "planned_end")
    list_filter = ("status", "priority", "task_type")
    search_fields = ("name", "legacy_code")


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "description", "task", "assignee", "due_date", "status")
    list_filter = ("status", "priority")
    search_fields = ("description", "legacy_code")


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "project", "target_date", "actual_date")
    search_fields = ("name", "legacy_code")


@admin.register(Sprint)
class SprintAdmin(SimpleHistoryAdmin):
    """History view shows who deleted a sprint and why (history_change_reason)."""
    list_display = ("name", "start_date", "end_date", "status", "is_active")
    list_filter = ("status", "is_active")
