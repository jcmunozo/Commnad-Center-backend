from rest_framework import serializers


class AuditReadMixin(serializers.Serializer):
    """Exposes audit fields as read-only on detail serializers."""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
