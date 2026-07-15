from rest_framework import serializers

from . import services
from .models import Ticket, TicketStatusLog


class TicketStatusLogSerializer(serializers.ModelSerializer):
    changed_by = serializers.CharField(source="changed_by.username", read_only=True, default=None)

    class Meta:
        model = TicketStatusLog
        fields = ("id", "from_status", "to_status", "changed_at", "changed_by")


class TicketListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="status_id", read_only=True)
    priority = serializers.CharField(source="priority_id", read_only=True)
    assignee_name = serializers.CharField(source="assignee.name", read_only=True, default=None)
    invested_hours = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ("id", "legacy_code", "ticket_number", "name", "status", "priority",
                  "assignee", "assignee_name", "invested_hours", "resolved_at", "created_at")

    def get_invested_hours(self, obj) -> float:
        return services.invested_hours(obj)


class TicketDetailSerializer(TicketListSerializer):
    status_logs = TicketStatusLogSerializer(many=True, read_only=True)

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + (
            "description", "status_logs", "custom_fields", "is_active", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class TicketWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "legacy_code", "ticket_number", "name", "description",
                  "priority", "status", "assignee", "custom_fields")

    def validate_ticket_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("ticket_number cannot be blank.")
        # objects (no active): los soft-borrados conservan el valor único en BD.
        qs = Ticket.objects.filter(ticket_number__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A ticket with this number already exists.")
        return value
