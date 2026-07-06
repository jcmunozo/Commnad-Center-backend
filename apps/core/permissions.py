"""Role-based permission primitives.

Roles are modeled as Django Groups (see ``accounts.management.commands.seed_roles``):
    - PMO Admin
    - Project Manager
    - Team Member
    - Viewer
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

ROLE_ADMIN = "PMO Admin"
ROLE_PM = "Project Manager"
ROLE_TEAM = "Team Member"
ROLE_VIEWER = "Viewer"


def user_in_roles(user, roles) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


class HasAnyRole(BasePermission):
    """Grant access if the user belongs to one of ``required_roles``.

    Subclass and set ``required_roles``, or build inline with :func:`role_required`.
    """

    required_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        return user_in_roles(request.user, self.required_roles)


def role_required(*roles):
    """Factory returning a permission class requiring any of ``roles``."""
    return type("RoleRequired", (HasAnyRole,), {"required_roles": tuple(roles)})


class ReadOnlyOrRoles(BasePermission):
    """Any authenticated user can read; only ``write_roles`` may write.

    Subclass and set ``write_roles``.
    """

    write_roles: tuple[str, ...] = (ROLE_ADMIN,)

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user_in_roles(request.user, self.write_roles)


class IsPMOAdmin(HasAnyRole):
    required_roles = (ROLE_ADMIN,)
