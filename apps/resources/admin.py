from django.contrib import admin

from .models import Employee, EmployeeShift, Holiday, Leave, TaskAssignment


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "name", "role", "level", "status", "location")
    list_filter = ("level", "status", "location")
    search_fields = ("name", "legacy_code")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "task", "employee", "assigned_date")


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "employee", "leave_type", "start_date", "end_date")
    list_filter = ("leave_type",)
    search_fields = ("employee__name", "legacy_code")


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "date", "name", "location")
    list_filter = ("location",)
    search_fields = ("name", "legacy_code")


@admin.register(EmployeeShift)
class EmployeeShiftAdmin(admin.ModelAdmin):
    list_display = ("employee", "weekday", "shift")
    list_filter = ("weekday", "shift")
