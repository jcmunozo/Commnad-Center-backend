from rest_framework import serializers

from apps.core.permissions import ROLE_ADMIN

from .models import Link

OWNER_FIELDS = ("project", "note", "ticket", "work_item")


class LinkSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, default=None)
    note_title = serializers.CharField(source="note.title", read_only=True, default=None)
    ticket_number = serializers.CharField(source="ticket.ticket_number", read_only=True, default=None)
    work_item_title = serializers.CharField(source="work_item.title", read_only=True, default=None)

    class Meta:
        model = Link
        fields = ("id", "url", "label", "description", "project", "project_name", "note", "note_title",
                  "ticket", "ticket_number", "work_item", "work_item_title",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")

    def _owner(self, field, attrs):
        return attrs[field] if field in attrs else getattr(self.instance, field, None)

    def validate(self, attrs):
        owners = [f for f in OWNER_FIELDS if self._owner(f, attrs) is not None]
        if len(owners) != 1:
            raise serializers.ValidationError(
                "A link must belong to exactly one of project, note, ticket, or work_item.")

        # Notes are personal (isolated by created_by elsewhere in the app) —
        # a link riding on someone else's note would quietly break that.
        note = self._owner("note", attrs)
        if note is not None:
            user = getattr(self.context.get("request"), "user", None)
            is_admin = user and (user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists())
            if not is_admin and note.created_by_id != getattr(user, "id", None):
                raise serializers.ValidationError("You can only add links to your own notes.")
        return attrs
