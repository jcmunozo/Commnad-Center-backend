from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Client
from .resources import ClientResource


@admin.register(Client)
class ClientAdmin(ImportExportModelAdmin):
    resource_class = ClientResource
    list_display = ("name", "contact_name", "is_active")
    search_fields = ("name", "contact_name")
