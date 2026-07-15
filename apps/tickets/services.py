"""Tiempo laboral invertido en tickets, derivado del log de estados.

Regla de negocio: el reloj corre solo mientras el ticket está en WIP,
dentro de una jornada fija de 8h (09:00-17:00 UTC, lunes a viernes).
Paused pausa; Resolved detiene. Mejora futura: usar el shift/timezone
del empleado en lugar de la ventana fija.

Este módulo no debe importar de ``apps.resources`` (resources.services
importa de aquí).
"""
from datetime import datetime, time, timedelta, timezone as dt_timezone

from django.utils import timezone

WIP = "WIP"
RESOLVED = "RESOLVED"
BUSINESS_DAY_START = 9
BUSINESS_DAY_END = 17  # 8h/día


def business_hours_between(start: datetime, end: datetime) -> float:
    """Horas de solape de [start, end] con la ventana 09:00-17:00 UTC lun-vie."""
    if not start or not end or end <= start:
        return 0.0
    total = timedelta()
    day = start.date()
    while day <= end.date():
        if day.isoweekday() <= 5:
            win_start = datetime.combine(day, time(BUSINESS_DAY_START), tzinfo=dt_timezone.utc)
            win_end = datetime.combine(day, time(BUSINESS_DAY_END), tzinfo=dt_timezone.utc)
            s, e = max(start, win_start), min(end, win_end)
            if e > s:
                total += e - s
        day += timedelta(days=1)
    return total.total_seconds() / 3600


def wip_intervals(logs, until: datetime) -> list[tuple[datetime, datetime]]:
    """Intervalos [inicio, fin) en WIP según los logs ordenados por changed_at.

    ``logs`` incluye la fila de creación (from_status=None). Un intervalo aún
    abierto (el ticket sigue en WIP) se cierra en ``until``.
    """
    intervals = []
    opened = None
    for log in logs:
        if log.to_status_id == WIP:
            if opened is None:
                opened = log.changed_at
        elif opened is not None:
            intervals.append((opened, log.changed_at))
            opened = None
    if opened is not None and until > opened:
        intervals.append((opened, until))
    return intervals


def invested_hours(ticket, until: datetime | None = None) -> float:
    """Horas laborales acumuladas en WIP para un ticket.

    Usa ``ticket.status_logs`` (prefetch en el viewset evita N+1); los logs
    ya vienen ordenados por ``changed_at`` (Meta.ordering).
    """
    until = until or timezone.now()
    logs = ticket.status_logs.all()
    return round(sum(business_hours_between(s, e) for s, e in wip_intervals(logs, until)), 2)


def _clipped_hours(logs, period_start: datetime, period_end: datetime) -> float:
    return sum(
        business_hours_between(max(s, period_start), min(e, period_end))
        for s, e in wip_intervals(logs, period_end)
    )


def employee_ticket_hours(period_start: datetime, period_end: datetime) -> dict[str, dict]:
    """Por empleado: horas WIP de sus tickets recortadas al período y tickets abiertos.

    Devuelve ``{employee_id(str): {"ticket_hours": float, "open_tickets": int}}``.
    """
    from .models import Ticket

    now = timezone.now()
    period_end = min(period_end, now)
    data: dict[str, dict] = {}
    tickets = (
        Ticket.active.filter(assignee__isnull=False)
        .prefetch_related("status_logs")
    )
    for ticket in tickets:
        row = data.setdefault(str(ticket.assignee_id), {"ticket_hours": 0.0, "open_tickets": 0})
        row["ticket_hours"] += _clipped_hours(ticket.status_logs.all(), period_start, period_end)
        if ticket.status_id != RESOLVED:
            row["open_tickets"] += 1
    for row in data.values():
        row["ticket_hours"] = round(row["ticket_hours"], 2)
    return data


def ticket_stats(employee_id=None) -> list[dict]:
    """Estadísticas de tickets por desarrollador (para /api/tickets/stats/)."""
    from apps.resources.models import Employee

    from .models import Ticket

    now = timezone.now()
    employees = Employee.active.all()
    if employee_id:
        employees = employees.filter(id=employee_id)

    tickets = Ticket.active.filter(assignee__in=employees).prefetch_related("status_logs")
    per_emp: dict = {}
    for t in tickets:
        agg = per_emp.setdefault(t.assignee_id, {
            "open_tickets": 0, "wip_tickets": 0, "paused_tickets": 0,
            "resolved_tickets": 0, "invested_hours": 0.0,
        })
        if t.status_id == RESOLVED:
            agg["resolved_tickets"] += 1
        else:
            agg["open_tickets"] += 1
            if t.status_id == WIP:
                agg["wip_tickets"] += 1
            else:
                agg["paused_tickets"] += 1
        agg["invested_hours"] += invested_hours(t, until=now)

    results = []
    for emp in employees:
        agg = per_emp.get(emp.id, {
            "open_tickets": 0, "wip_tickets": 0, "paused_tickets": 0,
            "resolved_tickets": 0, "invested_hours": 0.0,
        })
        agg["invested_hours"] = round(agg["invested_hours"], 2)
        results.append({"employee_id": str(emp.id), "name": emp.name, **agg})
    return results
