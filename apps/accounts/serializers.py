from rest_framework import serializers

from .models import AppUser


class MeSerializer(serializers.ModelSerializer):
    roles = serializers.ListField(source="role_names", read_only=True)

    class Meta:
        model = AppUser
        fields = ("id", "username", "email", "first_name", "last_name", "employee", "roles")
        read_only_fields = fields
