"""on_shift_now: live shift status in the workload rows."""
from datetime import datetime, timezone as tz
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.catalogs import models as cat
from apps.resources.models import EmployeeShift
from apps.resources.services import _on_shift_now, employee_workload
from tests.factories import EmployeeFactory

pytestmark = pytest.mark.django_db

NOON = datetime(2026, 3, 2, 12, 0, tzinfo=tz.utc)  # Monday 12:00 UTC


def _shift(start, end, name="Shift"):
    return SimpleNamespace(start_hour=start, end_hour=end, name=name)


def _emp(offset=None):
    timezone_ = SimpleNamespace(utc_offset=offset) if offset is not None else None
    return SimpleNamespace(timezone=timezone_)


# ----------------------------- unit: _on_shift_now -----------------------------
def test_inside_shift():
    assert _on_shift_now(_shift(9, 18), _emp(), NOON) is True


def test_outside_shift():
    assert _on_shift_now(_shift(14, 23), _emp(), NOON) is False


def test_no_shift_or_off_is_none():
    assert _on_shift_now(None, _emp(), NOON) is None
    assert _on_shift_now(_shift(None, None), _emp(), NOON) is None


def test_overnight_shift_wraps_midnight():
    night = _shift(22, 7)
    assert _on_shift_now(night, _emp(), NOON.replace(hour=23)) is True
    assert _on_shift_now(night, _emp(), NOON.replace(hour=3)) is True
    assert _on_shift_now(night, _emp(), NOON) is False


def test_uses_dev_local_time():
    # 12:00 UTC = 20:00 en UTC+8: fuera del turno 9-18 del dev
    assert _on_shift_now(_shift(9, 18), _emp(offset=8), NOON) is False
    # pero dentro del turno de tarde 14-23
    assert _on_shift_now(_shift(14, 23), _emp(offset=8), NOON) is True


def test_boundaries():
    assert _on_shift_now(_shift(12, 18), _emp(), NOON) is True   # inicio inclusive
    assert _on_shift_now(_shift(6, 12), _emp(), NOON) is False   # fin exclusivo


# ----------------------------- integración: employee_workload -----------------------------
def _catalog_shift(start, end):
    return cat.Shift.objects.get_or_create(
        code=f"T{start:02d}_{end:02d}",
        defaults={"name": f"{start:02d}:00 – {end:02d}:00",
                  "start_hour": start, "end_hour": end})[0]


def _row(emp):
    return next(r for r in employee_workload() if r["employee_id"] == str(emp.id))


def test_workload_row_reports_live_status(db):
    emp = EmployeeFactory()
    now = timezone.now()
    start, end = (now.hour - 1) % 24, (now.hour + 2) % 24
    EmployeeShift.objects.create(employee=emp, weekday=now.isoweekday(),
                                 shift=_catalog_shift(start, end))
    row = _row(emp)
    assert row["shift_today"] == f"{start:02d}:00 – {end:02d}:00"
    assert row["on_shift_now"] is True


def test_workload_row_without_shift_today(db):
    emp = EmployeeFactory()
    row = _row(emp)
    assert row["shift_today"] is None
    assert row["on_shift_now"] is None
