"""Per-user persisted sprint range for the Team page (/api/resources/workload-period/)."""
import pytest
from rest_framework.test import APIClient

from apps.resources.models import TeamWorkloadPeriod

pytestmark = pytest.mark.django_db


def test_get_creates_empty_row_on_first_access(pm_client, pm_user):
    res = pm_client.get("/api/resources/workload-period/")
    assert res.status_code == 200
    assert res.data == {"start_date": None, "end_date": None}
    assert TeamWorkloadPeriod.objects.get(user=pm_user).start_date is None


def test_put_persists_and_get_returns_it(pm_client):
    res = pm_client.put("/api/resources/workload-period/",
                        {"start_date": "2026-07-20", "end_date": "2026-08-02"},
                        format="json")
    assert res.status_code == 200
    assert res.data == {"start_date": "2026-07-20", "end_date": "2026-08-02"}

    res = pm_client.get("/api/resources/workload-period/")
    assert res.data == {"start_date": "2026-07-20", "end_date": "2026-08-02"}


def test_put_null_clears_the_range(pm_client):
    pm_client.put("/api/resources/workload-period/",
                  {"start_date": "2026-07-20", "end_date": "2026-08-02"}, format="json")
    res = pm_client.put("/api/resources/workload-period/",
                        {"start_date": None, "end_date": None}, format="json")
    assert res.status_code == 200
    assert res.data == {"start_date": None, "end_date": None}


def test_end_before_start_rejected(pm_client):
    res = pm_client.put("/api/resources/workload-period/",
                        {"start_date": "2026-08-02", "end_date": "2026-07-20"}, format="json")
    assert res.status_code == 400


def test_one_sided_range_rejected(pm_client):
    res = pm_client.put("/api/resources/workload-period/",
                        {"start_date": "2026-07-20", "end_date": None}, format="json")
    assert res.status_code == 400


def test_range_is_per_user(pm_client, admin_user):
    pm_client.put("/api/resources/workload-period/",
                  {"start_date": "2026-07-20", "end_date": "2026-08-02"}, format="json")

    admin_client = APIClient()
    admin_client.force_authenticate(admin_user)
    res = admin_client.get("/api/resources/workload-period/")
    assert res.data == {"start_date": None, "end_date": None}


def test_viewer_forbidden(viewer_client):
    res = viewer_client.get("/api/resources/workload-period/")
    assert res.status_code == 403


def test_anonymous_forbidden(api_client):
    res = api_client.get("/api/resources/workload-period/")
    assert res.status_code in (401, 403)
