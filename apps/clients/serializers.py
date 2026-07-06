from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "id", "legacy_code", "name", "contact_name", "contact_email", "notes",
            "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "is_active", "created_at", "updated_at")

    def validate_name(self, value):
        return value.strip()
