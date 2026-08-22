from django.contrib import admin

from .models import WorkItem, WorkItemMilestone, WorkItemTask


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "title", "project", "status", "priority", "is_active")
    list_filter = ("status", "priority")
    search_fields = ("legacy_code", "title", "description")


@admin.register(WorkItemTask)
class WorkItemTaskAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "work_item", "assignee", "status", "priority",
                    "is_active")
    list_filter = ("status", "priority")
    search_fields = ("legacy_code", "name")


@admin.register(WorkItemMilestone)
class WorkItemMilestoneAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "work_item", "owner_employee", "target_date",
                    "actual_date", "is_active")
    search_fields = ("legacy_code", "name")
