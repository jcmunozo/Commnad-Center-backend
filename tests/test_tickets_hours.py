"""Unit tests del motor de horas laborales de tickets.

Fechas de referencia (2026): lunes 2026-03-02 .. viernes 2026-03-06 son días
hábiles; 2026-03-07/08 es fin de semana. Ventana laboral: 09-17 UTC.
"""
from datetime import datetime, timezone as tz

import pytest

from apps.tickets import services
from apps.tickets.models import TicketStatusLog
from tests.factories import TicketFactory, seed_ticket_statuses, ticket_status

pytestmark = pytest.mark.django_db


def dt(day, hour, minute=0):
    return datetime(2026, 3, day, hour, minute, tzinfo=tz.utc)


# ----------------------------- business_hours_between -----------------------------
def test_same_day_inside_window():
    assert services.business_hours_between(dt(2, 10), dt(2, 15)) == 5.0


def test_clipped_to_window_edges():
    # 07:00 -> 20:00 solo cuenta 09-17
    assert services.business_hours_between(dt(2, 7), dt(2, 20)) == 8.0


def test_outside_window_is_zero():
    assert services.business_hours_between(dt(2, 18), dt(2, 20)) == 0.0


def test_weekend_excluded():
    # viernes 15:00 -> lunes 11:00 = 2h (vie) + 2h (lun)
    assert services.business_hours_between(dt(6, 15), dt(9, 11)) == 4.0


def test_full_week():
    # lunes 09:00 -> viernes 17:00 = 5 días x 8h
    assert services.business_hours_between(dt(2, 9), dt(6, 17)) == 40.0


def test_inverted_or_empty_range():
    assert services.business_hours_between(dt(2, 15), dt(2, 10)) == 0.0
    assert services.business_hours_between(None, dt(2, 10)) == 0.0


# ----------------------------- wip_intervals / invested_hours -----------------------------
def _log(ticket, to_code, when, from_code=None):
    return TicketStatusLog.objects.create(
        ticket=ticket, to_status=ticket_status(to_code),
        from_status=ticket_status(from_code) if from_code else None,
        changed_at=when)


def _ticket():
    seed_ticket_statuses()
    return TicketFactory()


def test_open_wip_interval_runs_until_now():
    ticket = _ticket()
    _log(ticket, "WIP", dt(2, 9))
    # martes 13:00 => lunes 8h + martes 4h
    assert services.invested_hours(ticket, until=dt(3, 13)) == 12.0


def test_paused_pauses_clock():
    ticket = _ticket()
    _log(ticket, "WIP", dt(2, 9))
    _log(ticket, "PAUSED", dt(2, 13), from_code="WIP")   # 4h en WIP
    # sigue pausado el resto de la semana
    assert services.invested_hours(ticket, until=dt(5, 17)) == 4.0


def test_resume_after_paused():
    ticket = _ticket()
    _log(ticket, "WIP", dt(2, 9))
    _log(ticket, "PAUSED", dt(2, 13), from_code="WIP")   # 4h
    _log(ticket, "WIP", dt(4, 9), from_code="PAUSED")    # reanuda miércoles
    _log(ticket, "RESOLVED", dt(4, 15), from_code="WIP")           # +6h
    assert services.invested_hours(ticket, until=dt(6, 17)) == 10.0


def test_resolved_stops_accumulating():
    ticket = _ticket()
    _log(ticket, "WIP", dt(2, 9))
    _log(ticket, "RESOLVED", dt(2, 17), from_code="WIP")
    assert services.invested_hours(ticket, until=dt(6, 17)) == 8.0


# ----------------------------- employee_ticket_hours -----------------------------
def test_employee_ticket_hours_clips_to_period():
    from tests.factories import EmployeeFactory

    seed_ticket_statuses()
    emp = EmployeeFactory()
    ticket = TicketFactory(assignee=emp, status=ticket_status("RESOLVED", is_closed=True))
    _log(ticket, "WIP", dt(2, 9))
    _log(ticket, "RESOLVED", dt(4, 17), from_code="WIP")  # lun+mar+mié = 24h

    data = services.employee_ticket_hours(dt(3, 0), dt(6, 23))  # desde martes
    row = data[str(emp.id)]
    assert row["ticket_hours"] == 16.0  # martes + miércoles
    assert row["open_tickets"] == 0
