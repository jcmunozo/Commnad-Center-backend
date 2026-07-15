"""Renombra el estado PENDING_CUSTOMER a PAUSED.

El código del catálogo es la clave primaria, así que hay que crear la fila
nueva, mover todas las referencias (tickets, historial y log de estados) y
borrar la vieja.
"""
from django.db import migrations

OLD, NEW = "PENDING_CUSTOMER", "PAUSED"


def forwards(apps, schema_editor):
    TicketStatus = apps.get_model("catalogs", "TicketStatus")
    Ticket = apps.get_model("tickets", "Ticket")
    HistoricalTicket = apps.get_model("tickets", "HistoricalTicket")
    TicketStatusLog = apps.get_model("tickets", "TicketStatusLog")

    old = TicketStatus.objects.filter(code=OLD).first()
    if old is None:
        return
    TicketStatus.objects.get_or_create(
        code=NEW,
        defaults={"name": "Paused", "sort_order": old.sort_order, "is_active": old.is_active})
    Ticket.objects.filter(status_id=OLD).update(status_id=NEW)
    HistoricalTicket.objects.filter(status_id=OLD).update(status_id=NEW)
    TicketStatusLog.objects.filter(from_status_id=OLD).update(from_status_id=NEW)
    TicketStatusLog.objects.filter(to_status_id=OLD).update(to_status_id=NEW)
    old.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0001_initial"),
        ("catalogs", "0002_ticketstatus"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
