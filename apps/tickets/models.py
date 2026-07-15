from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel


class Ticket(TimeStampedModel):
    """Ticket de soporte/incidencia, independiente de los proyectos.

    Los proyectos/servicios involucrados se describen en texto libre en
    ``description``. El tiempo invertido no se guarda: se deriva de los
    intervalos WIP en ``TicketStatusLog`` (ver services.invested_hours).
    """

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    ticket_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    priority = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    status = models.ForeignKey("catalogs.TicketStatus", on_delete=models.PROTECT,
                               related_name="+", default="WIP")
    assignee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                 on_delete=models.PROTECT, related_name="tickets")
    resolved_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        db_table = "ticket"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["ticket_number"]),
        ]

    def __str__(self):
        return f"{self.ticket_number} {self.name}".strip()


class TicketStatusLog(models.Model):
    """Transición de estado de un ticket; la fila inicial (from_status=None)
    se crea junto con el ticket para que el primer intervalo WIP arranque
    en la creación."""

    id = models.BigAutoField(primary_key=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.ForeignKey("catalogs.TicketStatus", null=True, blank=True,
                                    on_delete=models.PROTECT, related_name="+")
    to_status = models.ForeignKey("catalogs.TicketStatus", on_delete=models.PROTECT, related_name="+")
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+")

    class Meta:
        db_table = "ticket_status_log"
        ordering = ["changed_at"]
        indexes = [models.Index(fields=["ticket", "changed_at"])]

    def __str__(self):
        return f"{self.ticket_id}: {self.from_status_id} -> {self.to_status_id}"
