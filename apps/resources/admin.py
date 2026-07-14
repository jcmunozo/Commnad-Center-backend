from django.contrib import admin

from .models import Employee, EmployeeShift, TaskAssignment


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "role", "level", "status", "location")
    list_filter = ("level", "status", "location")
    search_fields = ("name", "legacy_code")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "task", "employee", "assigned_date")


@admin.register(EmployeeShift)
class EmployeeShiftAdmin(admin.ModelAdmin):
    list_display = ("employee", "weekday", "shift")
    list_filter = ("weekday", "shift")
