from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("legacy_code", "title", "category", "priority", "status",
                    "pinned", "due_date", "created_by", "is_active")
    list_filter = ("category", "priority", "status", "pinned")
    search_fields = ("legacy_code", "title", "content")
