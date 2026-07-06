from rest_framework import serializers


def build_catalog_serializer(model):
    """Return a ModelSerializer class exposing all fields of a catalog model."""
    meta = type("Meta", (), {"model": model, "fields": "__all__"})
    return type(f"{model.__name__}Serializer", (serializers.ModelSerializer,), {"Meta": meta})
