"""Create the four PMO role groups and attach model permissions.

    python manage.py seed_roles

Roles:
    PMO Admin        -> all permissions (superuser-like via group)
    Project Manager  -> add/change/view across delivery apps; no destructive catalog edits
    Team Member      -> add/change/view on tasks & tracking; view elsewhere
    Viewer           -> view only
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_TEAM, ROLE_VIEWER

DELIVERY_APPS = ("projects", "resources", "tracking", "clients")


class Command(BaseCommand):
    help = "Seed PMO role groups and permissions."

    def handle(self, *args, **options):
        perms = Permission.objects.select_related("content_type")

        # --- PMO Admin: everything ---
        admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        admin_group.permissions.set(perms.all())

        # --- Project Manager: full delivery, view catalogs ---
        pm_group, _ = Group.objects.get_or_create(name=ROLE_PM)
        pm_perms = perms.filter(content_type__app_label__in=DELIVERY_APPS)
        pm_group.permissions.set(pm_perms)

        # --- Team Member: write tasks/tracking, view rest ---
        team_group, _ = Group.objects.get_or_create(name=ROLE_TEAM)
        team_write = perms.filter(
            content_type__app_label__in=("projects", "tracking"),
            codename__regex=r"^(add|change|view)_",
        )
        team_view = perms.filter(codename__startswith="view_")
        team_group.permissions.set(team_write.union(team_view))

        # --- Viewer: view only ---
        viewer_group, _ = Group.objects.get_or_create(name=ROLE_VIEWER)
        viewer_group.permissions.set(perms.filter(codename__startswith="view_"))

        self.stdout.write(self.style.SUCCESS("Seeded roles: Admin, PM, Team, Viewer."))
