from django.contrib import admin

from .models import Link


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("label", "url", "project", "note", "ticket", "work_item", "is_active")
    search_fields = ("label", "url")
