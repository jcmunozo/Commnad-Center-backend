"""Workload computation: task hours prorated across collaborators (Fase 2)."""
from datetime import date, datetime, time, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from apps.projects.models import Task
from apps.tickets.services import employee_ticket_hours

from .models import Employee, EmployeeShift, Holiday, Leave, TaskAssignment

ACTIVE_TASK_EXCLUDE = ("DONE", "CANCELLED")
DEFAULT_WORKDAYS = frozenset({1, 2, 3, 4, 5})  # Mon..Fri when no schedule exists
CALENDAR_MAX_DAYS = 366


def employee_workload(period_start=None, period_end=None) -> list[dict]:
    """Return prorated assigned hours, capacity and workload % per active employee.

    Each active task's ``estimated_hours`` is split equally among its active
    assignees; every employee accumulates their share over active tasks.
    Optional ``period_*`` filters by the task's planned window.

    Ticket WIP hours (clipped to the period; defaults to the current ISO week
    so lifetime hours aren't compared against weekly capacity) add to
    ``assigned_hours`` and therefore to ``workload_pct``/``alert``.
    """
    now = timezone.now()
    ticket_start = period_start or _start_of_iso_week(now)
    ticket_end = period_end or now
    ticket_data = employee_ticket_hours(ticket_start, ticket_end)

    task_qs = Task.active.exclude(status_id__in=ACTIVE_TASK_EXCLUDE)
    if period_start:
        task_qs = task_qs.filter(planned_end__gte=period_start)
    if period_end:
        task_qs = task_qs.filter(planned_start__lte=period_end)

    # collaborators per task
    counts = {
        row["task"]: row["n"]
        for row in TaskAssignment.active.filter(task__in=task_qs)
        .values("task").annotate(n=Count("id"))
    }

    shares: dict[str, Decimal] = {}
    open_tasks: dict[str, int] = {}
    assignments = (
        TaskAssignment.active.filter(task__in=task_qs)
        .select_related("task", "employee")
    )
    for a in assignments:
        n = counts.get(a.task_id, 1) or 1
        est = a.task.estimated_hours or Decimal(0)
        shares[a.employee_id] = shares.get(a.employee_id, Decimal(0)) + est / n
        open_tasks[a.employee_id] = open_tasks.get(a.employee_id, 0) + 1

    # turno de hoy por empleado (semana actual; ISO 1=lunes)
    today_date = timezone.localdate()
    today = today_date.isoweekday()
    shift_today = {
        s.employee_id: s.shift
        for s in EmployeeShift.objects.filter(weekday=today).select_related("shift")
    }

    # leaves: capacity drops per working day off within the queried period
    # (default: the full current ISO week, so upcoming days count too)
    leave_start = period_start.date() if period_start else _start_of_iso_week(now).date()
    leave_end = period_end.date() if period_end else leave_start + timedelta(days=6)
    working_weekdays = _working_weekdays()
    leave_dates = _leave_dates(leave_start, leave_end)
    holiday_dates = _holiday_dates(leave_start, leave_end)
    # "today" is each employee's calendar date, not the server's (UTC): a leave
    # starting tomorrow must not flag a UTC-5 dev the evening before. ±1 day
    # covers every possible tz offset around the server date.
    recent_leave_dates = _leave_dates(today_date - timedelta(days=1),
                                      today_date + timedelta(days=1))
    recent_holiday_dates = _holiday_dates(today_date - timedelta(days=1),
                                          today_date + timedelta(days=1))

    results = []
    for emp in Employee.active.select_related("timezone", "location").all():
        tickets = ticket_data.get(str(emp.id), {})
        ticket_hours = tickets.get("ticket_hours", 0.0)
        assigned = shares.get(emp.id, Decimal(0)) + Decimal(str(ticket_hours))
        capacity = emp.capacity_hours or Decimal(0)
        workdays = working_weekdays.get(emp.id, DEFAULT_WORKDAYS)
        emp_holidays = holiday_dates.get(emp.location_id, set())
        leave_days = sum(1 for d in leave_dates.get(emp.id, ())
                         if d.isoweekday() in workdays)
        holiday_days = sum(1 for d in emp_holidays if d.isoweekday() in workdays)
        # a leave overlapping a holiday is a single day off, not two
        off_days = sum(1 for d in leave_dates.get(emp.id, set()) | emp_holidays
                       if d.isoweekday() in workdays)
        if capacity and workdays and off_days:
            capacity = max(Decimal(0),
                           capacity - capacity / len(workdays) * off_days)
        workload = float(assigned / capacity) if capacity else 0.0
        shift = shift_today.get(emp.id)
        local_today = _local_today(emp, now)
        is_off = local_today in recent_leave_dates.get(emp.id, ())
        is_holiday = local_today in recent_holiday_dates.get(emp.location_id, ())
        results.append({
            "employee_id": str(emp.id),
            "name": emp.name,
            "location": emp.location_id,
            "location_name": emp.location.name if emp.location_id else None,
            "assigned_hours": round(float(assigned), 2),
            "capacity_hours": round(float(capacity), 2),
            "workload_pct": round(workload, 4),
            "alert": _alert(workload),
            "shift_today": shift.name if shift else None,
            "on_shift_now": False if (is_off or is_holiday) else _on_shift_now(shift, emp, now),
            "open_tasks": open_tasks.get(emp.id, 0),
            "ticket_hours": round(ticket_hours, 2),
            "open_tickets": tickets.get("open_tickets", 0),
            "on_leave_today": is_off,
            "leave_days": leave_days,
            "holiday_today": is_holiday,
            "holiday_days": holiday_days,
        })
    return results


def leave_calendar(start: date, end: date, threshold: float | None = None) -> list[dict]:
    """Per-day absence summary between ``start`` and ``end`` (inclusive).

    Only working days count: an employee shows as absent only on weekdays they
    actually work (non-OFF shift; fallback Mon–Fri), and ``headcount`` is the
    number of active employees scheduled that weekday — so weekends don't
    produce absences or alerts. Public holidays behave like a per-country
    weekend: everyone in a ``Holiday``'s Location drops out of that day's
    headcount (and their leaves don't count), and the day carries the holiday
    list so the UI can flag it. Every day in the range is still returned so a
    calendar can be painted directly. ``alert`` flips to OVER_THRESHOLD when
    the share of the scheduled roster on leave exceeds ``threshold``
    (default: ``settings.LEAVE_ALERT_PCT``).
    """
    if end < start:
        raise ValueError("end must be on or after start.")
    if (end - start).days + 1 > CALENDAR_MAX_DAYS:
        raise ValueError(f"Range too large (max {CALENDAR_MAX_DAYS} days).")
    if threshold is None:
        threshold = settings.LEAVE_ALERT_PCT

    working_weekdays = _working_weekdays()
    holidays_by_day = _holidays(start, end)
    holiday_locs = {d: {h["location"] for h in hs} for d, hs in holidays_by_day.items()}
    headcount_by_weekday = dict.fromkeys(range(1, 8), 0)
    loc_weekday_count: dict[tuple[str, int], int] = {}
    for emp_id, loc in Employee.active.values_list("id", "location_id"):
        for wd in working_weekdays.get(emp_id, DEFAULT_WORKDAYS):
            headcount_by_weekday[wd] += 1
            if loc:
                loc_weekday_count[(loc, wd)] = loc_weekday_count.get((loc, wd), 0) + 1

    by_day: dict[date, list[dict]] = {}
    leaves = (Leave.active.filter(start_date__lte=end, end_date__gte=start,
                                  employee__is_active=True)
              .select_related("employee", "leave_type"))
    for lv in leaves:
        workdays = working_weekdays.get(lv.employee_id, DEFAULT_WORKDAYS)
        d = max(lv.start_date, start)
        last = min(lv.end_date, end)
        while d <= last:
            if (d.isoweekday() in workdays
                    and lv.employee.location_id not in holiday_locs.get(d, ())):
                by_day.setdefault(d, []).append({
                    "employee_id": str(lv.employee_id),
                    "name": lv.employee.name,
                    "leave_type": lv.leave_type.name,
                })
            d += timedelta(days=1)

    days = []
    d = start
    while d <= end:
        absent = sorted(by_day.get(d, []), key=lambda a: a["name"])
        # same employee may have overlapping leave rows: count people, not rows
        n = len({a["employee_id"] for a in absent})
        wd = d.isoweekday()
        headcount = headcount_by_weekday[wd]
        for loc in holiday_locs.get(d, ()):
            headcount -= loc_weekday_count.get((loc, wd), 0)
        pct = n / headcount if headcount else 0.0
        days.append({
            "date": d,
            "absent": absent,
            "absent_count": n,
            "headcount": headcount,
            "absent_pct": round(pct, 4),
            "alert": "OVER_THRESHOLD" if pct > threshold else "OK",
            "holidays": holidays_by_day.get(d, []),
        })
        d += timedelta(days=1)
    return days


def _local_today(emp, now) -> date:
    """The employee's current calendar date: UTC now shifted by their tz offset."""
    offset = float(emp.timezone.utc_offset) if emp.timezone else 0.0
    return (now + timedelta(hours=offset)).date()


def _working_weekdays() -> dict[str, set[int]]:
    """Employee -> ISO weekdays with a real (non-OFF) shift scheduled."""
    days: dict[str, set[int]] = {}
    for s in EmployeeShift.objects.select_related("shift"):
        if s.shift.start_hour is None:  # OFF entries are not working days
            continue
        days.setdefault(s.employee_id, set()).add(s.weekday)
    return days


def _leave_dates(start: date, end: date) -> dict[str, set[date]]:
    """Employee -> distinct dates on leave within [start, end]."""
    dates: dict[str, set[date]] = {}
    leaves = Leave.active.filter(start_date__lte=end, end_date__gte=start,
                                 employee__is_active=True)
    for lv in leaves:
        d = max(lv.start_date, start)
        last = min(lv.end_date, end)
        bucket = dates.setdefault(lv.employee_id, set())
        while d <= last:
            bucket.add(d)
            d += timedelta(days=1)
    return dates


def _holiday_dates(start: date, end: date) -> dict[str, set[date]]:
    """Location code -> holiday dates within [start, end]."""
    dates: dict[str, set[date]] = {}
    for h in Holiday.active.filter(date__gte=start, date__lte=end):
        dates.setdefault(h.location_id, set()).add(h.date)
    return dates


def _holidays(start: date, end: date) -> dict[date, list[dict]]:
    """Date -> holidays that day, one entry per country (Location)."""
    by_day: dict[date, list[dict]] = {}
    qs = Holiday.active.filter(date__gte=start, date__lte=end).select_related("location")
    for h in qs:
        by_day.setdefault(h.date, []).append({
            "location": h.location_id,
            "location_name": h.location.name,
            "name": h.name,
        })
    return by_day


def _on_shift_now(shift, emp, now) -> bool | None:
    """Whether the employee is inside today's shift right now.

    Shift hours are the dev's local time; ``emp.timezone.utc_offset`` converts
    the current UTC time. None when there is no shift today or the shift has
    no hours (OFF). Overnight shifts (start > end) wrap past midnight.
    """
    if shift is None or shift.start_hour is None or shift.end_hour is None:
        return None
    offset = float(emp.timezone.utc_offset) if emp.timezone else 0.0
    local = (now.hour + now.minute / 60 + offset) % 24
    start, end = shift.start_hour, shift.end_hour
    if start <= end:
        return start <= local < end
    return local >= start or local < end


def _start_of_iso_week(now: datetime) -> datetime:
    monday = now.date() - timedelta(days=now.isoweekday() - 1)
    return datetime.combine(monday, time.min, tzinfo=dt_timezone.utc)


def _alert(workload: float) -> str:
    if workload > 1.0:
        return "OVERLOADED"
    if workload > 0.85:
        return "HIGH_LOAD"
    return "OK"
