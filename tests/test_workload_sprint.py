"""Sprint-length periods: capacity must scale with the actual workdays in the
queried start/end window, not stay pinned to a single week's weekly_hours.
The 42h week is 9-9-9-9-6 (Fri is short), not an even 8.4h/day split, so
weighted days matter both for period scaling and for leave/holiday deduction."""
from datetime import date, datetime, timedelta
from datetime import timezone as tz

import pytest

from apps.resources.services import employee_workload
from tests.factories import EmployeeFactory, LeaveFactory

pytestmark = pytest.mark.django_db

MON = datetime(2026, 3, 2, 0, tzinfo=tz.utc)  # Monday


def _row(emp, start, end):
    rows = employee_workload(period_start=start, period_end=end)
    return next(r for r in rows if r["employee_id"] == str(emp.id))


def _weighted_workdays(start: date, end: date) -> int:
    """Mirrors the 9-9-9-9-6 split independently of the implementation."""
    total, d = 0, start
    while d <= end:
        wd = d.isoweekday()
        if wd <= 4:
            total += 9
        elif wd == 5:
            total += 6
        d += timedelta(days=1)
    return total


def test_one_week_period_matches_weekly_hours(db):
    emp = EmployeeFactory(weekly_hours=42)
    row = _row(emp, MON, MON + timedelta(days=4))  # Mon..Fri
    assert row["capacity_hours"] == 42.0


def test_two_week_sprint_doubles_capacity(db):
    emp = EmployeeFactory(weekly_hours=42)
    row = _row(emp, MON, MON + timedelta(days=11))  # Mar 2-6 + Mar 9-13
    assert row["capacity_hours"] == 84.0


def test_fifteen_day_sprint_scales_to_actual_workdays(db):
    emp = EmployeeFactory(weekly_hours=42)
    start = MON + timedelta(days=2)  # Wednesday
    end = start + timedelta(days=14)  # 15 calendar days
    expected = _weighted_workdays(start.date(), end.date())
    row = _row(emp, start, end)
    assert row["capacity_hours"] == pytest.approx(expected)


def test_tuesday_leave_costs_a_full_day(db):
    emp = EmployeeFactory(weekly_hours=42)
    end = MON + timedelta(days=11)  # two-week sprint, 84h capacity
    LeaveFactory(employee=emp, start_date=(MON + timedelta(days=8)).date(),
                 end_date=(MON + timedelta(days=8)).date())  # a Tuesday off
    row = _row(emp, MON, end)
    assert row["capacity_hours"] == pytest.approx(84 - 9)
    assert row["leave_days"] == 1


def test_friday_leave_costs_less_than_a_regular_day(db):
    emp = EmployeeFactory(weekly_hours=42)
    end = MON + timedelta(days=11)  # two-week sprint, 84h capacity
    LeaveFactory(employee=emp, start_date=(MON + timedelta(days=4)).date(),
                 end_date=(MON + timedelta(days=4)).date())  # a Friday off
    row = _row(emp, MON, end)
    assert row["capacity_hours"] == pytest.approx(84 - 6)
    assert row["leave_days"] == 1
