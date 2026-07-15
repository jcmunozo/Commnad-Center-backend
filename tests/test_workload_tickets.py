"""Integración tickets → workload: las horas WIP suman a assigned_hours."""
from datetime import datetime, timezone as tz

import pytest

from apps.resources.services import employee_workload
from apps.tickets.models import TicketStatusLog
from tests.factories import (
    EmployeeFactory,
    TicketFactory,
    seed_ticket_statuses,
    ticket_status,
)

pytestmark = pytest.mark.django_db

# lunes y miércoles hábiles (ver test_tickets_hours)
MON = datetime(2026, 3, 2, 9, tzinfo=tz.utc)
WED = datetime(2026, 3, 4, 17, tzinfo=tz.utc)
FRI = datetime(2026, 3, 6, 23, tzinfo=tz.utc)


def _wip_ticket(emp, start=MON):
    ticket = TicketFactory(assignee=emp)
    TicketStatusLog.objects.create(ticket=ticket, from_status=None,
                                   to_status=ticket_status("WIP"), changed_at=start)
    return ticket


def _row(emp, start=MON, end=FRI):
    rows = employee_workload(period_start=start, period_end=end)
    return next(r for r in rows if r["employee_id"] == str(emp.id))


def test_wip_ticket_hours_add_to_assigned(db):
    seed_ticket_statuses()
    emp = EmployeeFactory()
    ticket = _wip_ticket(emp)
    TicketStatusLog.objects.create(ticket=ticket, from_status=ticket_status("WIP"),
                                   to_status=ticket_status("RESOLVED"), changed_at=WED)
    ticket.status = ticket_status("RESOLVED")
    ticket.save()

    row = _row(emp)
    assert row["ticket_hours"] == 24.0  # lun+mar+mié
    assert row["assigned_hours"] == 24.0  # sin tareas: solo tickets
    assert row["open_tickets"] == 0


def test_open_ticket_counts(db):
    seed_ticket_statuses()
    emp = EmployeeFactory()
    _wip_ticket(emp)
    row = _row(emp)
    assert row["open_tickets"] == 1
    assert row["ticket_hours"] > 0


def test_ticket_hours_can_overload(db):
    seed_ticket_statuses()
    emp = EmployeeFactory(weekly_hours=10)  # capacidad baja
    ticket = _wip_ticket(emp)
    TicketStatusLog.objects.create(ticket=ticket, from_status=ticket_status("WIP"),
                                   to_status=ticket_status("RESOLVED"), changed_at=WED)

    row = _row(emp)
    assert row["workload_pct"] > 1.0
    assert row["alert"] == "OVERLOADED"


def test_employee_without_tickets_unaffected(db):
    seed_ticket_statuses()
    emp = EmployeeFactory()
    row = _row(emp)
    assert row["ticket_hours"] == 0.0
    assert row["open_tickets"] == 0
    assert row["assigned_hours"] == 0.0
