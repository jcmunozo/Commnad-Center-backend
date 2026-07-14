from rest_framework import viewsets

from .permissions import ROLE_ADMIN, ROLE_PM, role_required


def next_legacy_code(model, prefix: str) -> str:
    """Next PREFIX-NNN scanning ALL rows: soft-deleted records keep their
    unique legacy_code, so the active manager alone would produce collisions."""
    last = (model.objects.filter(legacy_code__regex=rf"^{prefix}-\d+$")
            .order_by("-legacy_code")
            .values_list("legacy_code", flat=True).first())
    n = int(last.split("-")[1]) + 1 if last else 1
    return f"{prefix}-{n:03d}"


class BaseModelViewSet(viewsets.ModelViewSet):
    """Shared behavior for domain viewsets.

    - Operates on live rows by default (``model.active``).
    - Performs soft-delete instead of physical delete.
    - Stamps ``created_by`` / ``updated_by`` from the request user.
    - Per-action permissions: reads for any authenticated user, writes for
      ``write_roles`` (default: PMO Admin + Project Manager).
    - When ``legacy_prefix`` is set, autogenerates the next PREFIX-NNN
      legacy_code on create if the payload omits it.
    """

    write_roles = (ROLE_ADMIN, ROLE_PM)
    legacy_prefix: str | None = None

    def get_queryset(self):
        model = self.serializer_class.Meta.model
        manager = getattr(model, "active", model.objects)
        return manager.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [role_required(*self.write_roles)()]
        return super().get_permissions()

    def perform_create(self, serializer):
        if self.legacy_prefix and not serializer.validated_data.get("legacy_code"):
            serializer.validated_data["legacy_code"] = next_legacy_code(
                serializer.Meta.model, self.legacy_prefix)
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()
        else:
            instance.delete()
