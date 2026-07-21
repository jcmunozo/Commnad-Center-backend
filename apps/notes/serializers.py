from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, default=None)
    project_code = serializers.CharField(source="project.legacy_code", read_only=True, default=None)

    class Meta:
        model = Note
        fields = (
            "id", "legacy_code", "title", "content", "pinned", "due_date",
            "category", "priority", "status", "project", "project_name",
            "project_code", "custom_fields", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "legacy_code", "is_active", "created_at", "updated_at")
