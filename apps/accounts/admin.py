from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AppUser


@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PMO", {"fields": ("employee",)}),)
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
