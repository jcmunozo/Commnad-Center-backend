from rest_framework import viewsets

from apps.core.permissions import ROLE_ADMIN, ReadOnlyOrRoles

from .serializers import build_catalog_serializer


class _CatalogPermission(ReadOnlyOrRoles):
    write_roles = (ROLE_ADMIN,)  # only PMO Admin edits catalogs


def build_catalog_viewset(model):
    """Return a ModelViewSet for a catalog model (read for all, write for Admin)."""
    serializer_cls = build_catalog_serializer(model)

    attrs = {
        "queryset": model.objects.all(),
        "serializer_class": serializer_cls,
        "permission_classes": [_CatalogPermission],
        "filterset_fields": ["is_active"],
        "search_fields": ["code", "name"],
        "ordering_fields": ["sort_order", "name", "code"],
        "__doc__": f"CRUD for the {model._meta.verbose_name} catalog.",
    }
    return type(f"{model.__name__}ViewSet", (viewsets.ModelViewSet,), attrs)
