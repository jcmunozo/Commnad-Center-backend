from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_TEAM, user_in_roles

WRITE_ROLES = (ROLE_ADMIN, ROLE_PM, ROLE_TEAM)


class LinkPermission(BasePermission):
    """Reads: any authenticated user (the queryset already hides links on
    someone else's private note). Writes: the regular Task/SubTask roles —
    except a link on a Note, which mirrors NoteViewSet and stays open to
    that note's own creator regardless of role (ownership is enforced in
    the serializer for create; here for update/delete on an existing row)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        if view.action == "create" and request.data.get("note"):
            return True
        return user_in_roles(user, WRITE_ROLES)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if obj.note_id:
            return obj.note.created_by_id == request.user.id or user_in_roles(request.user, (ROLE_ADMIN,))
        return user_in_roles(request.user, WRITE_ROLES)
