from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, role_required
from apps.core.views import BaseModelViewSet

from . import services
from .filters import TicketFilter
from .models import Ticket, TicketStatusLog
from .serializers import (
    TicketDetailSerializer,
    TicketListSerializer,
    TicketStatusLogSerializer,
    TicketWriteSerializer,
)


class TicketViewSet(BaseModelViewSet):
    """Support tickets with a status log and derived invested hours."""

    legacy_prefix = "TCK"
    filterset_class = TicketFilter
    search_fields = ["name", "ticket_number", "legacy_code", "description"]
    ordering_fields = ["created_at", "ticket_number", "resolved_at"]
    serializer_class = TicketDetailSerializer

    def get_queryset(self):
        return (
            Ticket.active.select_related("assignee", "status", "priority")
            .prefetch_related("status_logs")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action in ("create", "update", "partial_update"):
            return TicketWriteSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)
        ticket = serializer.instance
        if ticket.status_id == services.RESOLVED:
            ticket.resolved_at = ticket.created_at
            ticket.save(update_fields=["resolved_at", "updated_at"])
        TicketStatusLog.objects.create(
            ticket=ticket, from_status=None, to_status=ticket.status,
            changed_at=ticket.created_at, changed_by=self.request.user)

    def perform_update(self, serializer):
        old_status_id = serializer.instance.status_id
        super().perform_update(serializer)
        ticket = serializer.instance
        if ticket.status_id == old_status_id:
            return
        now = timezone.now()
        TicketStatusLog.objects.create(
            ticket=ticket, from_status_id=old_status_id, to_status=ticket.status,
            changed_at=now, changed_by=self.request.user)
        new_resolved_at = now if ticket.status_id == services.RESOLVED else None
        if ticket.resolved_at != new_resolved_at:
            ticket.resolved_at = new_resolved_at
            ticket.save(update_fields=["resolved_at", "updated_at"])

    @extend_schema(responses=TicketStatusLogSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="status-log")
    def status_log(self, request, pk=None):
        """Status transition history for the ticket."""
        logs = self.get_object().status_logs.select_related("changed_by")
        return Response(TicketStatusLogSerializer(logs, many=True).data)

    @extend_schema(parameters=[OpenApiParameter("employee", str, description="Filter by employee UUID")])
    @action(detail=False, methods=["get"],
            permission_classes=[role_required(ROLE_ADMIN, ROLE_PM)])
    def stats(self, request):
        """Per-developer ticket statistics (counts + invested hours)."""
        return Response(services.ticket_stats(employee_id=request.query_params.get("employee")))
