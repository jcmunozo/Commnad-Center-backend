from django.contrib import admin

from .models import Ticket, TicketStatusLog


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "name", "status", "priority", "assignee", "is_active")
    list_filter = ("status", "priority")
    search_fields = ("ticket_number", "name", "legacy_code")


@admin.register(TicketStatusLog)
class TicketStatusLogAdmin(admin.ModelAdmin):
    list_display = ("ticket", "from_status", "to_status", "changed_at", "changed_by")
    list_filter = ("to_status",)
