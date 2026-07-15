import pytest

from apps.tickets.models import Ticket
from tests.factories import EmployeeFactory, seed_ticket_statuses, sev

pytestmark = pytest.mark.django_db


def _body(**overrides):
    seed_ticket_statuses()
    body = {"ticket_number": "INC-2026-001", "name": "Payment API down",
            "priority": sev().code}
    body.update(overrides)
    return body


def test_create_autogenerates_code_and_initial_log(pm_client):
    resp = pm_client.post("/api/tickets/", _body(), format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["legacy_code"] == "TCK-001"
    assert data["status"] == "WIP"

    detail = pm_client.get(f"/api/tickets/{data['id']}/").json()
    assert detail["invested_hours"] >= 0.0
    assert detail["status"] == "WIP"

    ticket = Ticket.objects.get(pk=data["id"])
    logs = list(ticket.status_logs.all())
    assert len(logs) == 1
    assert logs[0].from_status_id is None and logs[0].to_status_id == "WIP"
    assert logs[0].changed_at == ticket.created_at


def test_duplicate_ticket_number_rejected(pm_client):
    assert pm_client.post("/api/tickets/", _body(), format="json").status_code == 201
    resp = pm_client.post("/api/tickets/", _body(name="Otro"), format="json")
    assert resp.status_code == 400
    assert "ticket_number" in resp.json()


def test_ticket_number_is_editable(pm_client):
    ticket_id = pm_client.post("/api/tickets/", _body(), format="json").json()["id"]
    resp = pm_client.patch(f"/api/tickets/{ticket_id}/",
                           {"ticket_number": "INC-2026-999"}, format="json")
    assert resp.status_code == 200
    assert Ticket.objects.get(pk=ticket_id).ticket_number == "INC-2026-999"


def test_status_change_writes_log_and_resolved_at(pm_client):
    ticket_id = pm_client.post("/api/tickets/", _body(), format="json").json()["id"]

    resp = pm_client.patch(f"/api/tickets/{ticket_id}/",
                           {"status": "PAUSED"}, format="json")
    assert resp.status_code == 200
    ticket = Ticket.objects.get(pk=ticket_id)
    assert ticket.status_logs.count() == 2
    assert ticket.resolved_at is None

    pm_client.patch(f"/api/tickets/{ticket_id}/", {"status": "RESOLVED"}, format="json")
    ticket.refresh_from_db()
    assert ticket.status_logs.count() == 3
    assert ticket.resolved_at is not None

    # reabrir limpia resolved_at
    pm_client.patch(f"/api/tickets/{ticket_id}/", {"status": "WIP"}, format="json")
    ticket.refresh_from_db()
    assert ticket.resolved_at is None
    assert ticket.status_logs.count() == 4


def test_non_status_patch_writes_no_log(pm_client):
    ticket_id = pm_client.post("/api/tickets/", _body(), format="json").json()["id"]
    pm_client.patch(f"/api/tickets/{ticket_id}/", {"name": "Renamed"}, format="json")
    assert Ticket.objects.get(pk=ticket_id).status_logs.count() == 1


def test_status_log_endpoint(pm_client):
    ticket_id = pm_client.post("/api/tickets/", _body(), format="json").json()["id"]
    pm_client.patch(f"/api/tickets/{ticket_id}/", {"status": "RESOLVED"}, format="json")
    resp = pm_client.get(f"/api/tickets/{ticket_id}/status-log/")
    assert resp.status_code == 200
    rows = resp.json()
    assert [r["to_status"] for r in rows] == ["WIP", "RESOLVED"]


def test_filters_and_search(pm_client):
    emp = EmployeeFactory()
    pm_client.post("/api/tickets/", _body(assignee=str(emp.id)), format="json")
    pm_client.post("/api/tickets/",
                   _body(ticket_number="INC-2026-002", name="Login bug",
                         status="RESOLVED"), format="json")

    assert pm_client.get("/api/tickets/?status=RESOLVED").json()["count"] == 1
    assert pm_client.get("/api/tickets/?open=true").json()["count"] == 1
    assert pm_client.get(f"/api/tickets/?assignee={emp.id}").json()["count"] == 1
    assert pm_client.get("/api/tickets/?search=INC-2026-002").json()["count"] == 1


def test_viewer_cannot_write(api_client, pm_user, viewer_user):
    # pm_client y viewer_client comparten APIClient: autenticar por turnos
    api_client.force_authenticate(pm_user)
    ticket_id = api_client.post("/api/tickets/", _body(), format="json").json()["id"]

    api_client.force_authenticate(viewer_user)
    assert api_client.post("/api/tickets/", _body(ticket_number="INC-X"),
                           format="json").status_code == 403
    assert api_client.patch(f"/api/tickets/{ticket_id}/", {"name": "n"},
                            format="json").status_code == 403
    # lectura sí permitida
    assert api_client.get("/api/tickets/").status_code == 200


def test_delete_is_soft(pm_client):
    ticket_id = pm_client.post("/api/tickets/", _body(), format="json").json()["id"]
    assert pm_client.delete(f"/api/tickets/{ticket_id}/").status_code == 204
    ticket = Ticket.objects.get(pk=ticket_id)
    assert ticket.is_active is False
    assert pm_client.get("/api/tickets/").json()["count"] == 0


def test_stats_endpoint(pm_client):
    emp = EmployeeFactory()
    pm_client.post("/api/tickets/", _body(assignee=str(emp.id)), format="json")
    pm_client.post("/api/tickets/",
                   _body(ticket_number="INC-2", assignee=str(emp.id),
                         status="RESOLVED"), format="json")
    resp = pm_client.get("/api/tickets/stats/")
    assert resp.status_code == 200
    row = next(r for r in resp.json() if r["employee_id"] == str(emp.id))
    assert row["open_tickets"] == 1
    assert row["wip_tickets"] == 1
    assert row["resolved_tickets"] == 1
    assert "invested_hours" in row
