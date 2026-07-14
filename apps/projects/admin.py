from django.contrib import admin

from .models import Milestone, Project, SubTask, Task


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
