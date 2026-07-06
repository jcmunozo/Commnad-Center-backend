from rest_framework import viewsets

from .permissions import ROLE_ADMIN, ROLE_PM, role_required


class BaseModelViewSet(viewsets.ModelViewSet):
    """Shared behavior for domain viewsets.

    - Operates on live rows by default (``model.active``).
    - Performs soft-delete instead of physical delete.
    - Stamps ``created_by`` / ``updated_by`` from the request user.
    - Per-action permissions: reads for any authenticated user, writes for
      ``write_roles`` (default: PMO Admin + Project Manager).
    """

    write_roles = (ROLE_ADMIN, ROLE_PM)

    def get_queryset(self):
        model = self.serializer_class.Meta.model
        manager = getattr(model, "active", model.objects)
        return manager.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [role_required(*self.write_roles)()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()
        else:
            instance.delete()
