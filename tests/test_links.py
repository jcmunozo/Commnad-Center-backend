"""Reference links attached to exactly one of Project/Note/Ticket/WorkItem."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .factories import ProjectFactory, TicketFactory, WorkItemFactory, seed_ticket_statuses

pytestmark = pytest.mark.django_db

User = get_user_model()


def _roleless_client(username="alice"):
    user = User.objects.create_user(username=username, password="x")
    client = APIClient()
    client.force_authenticate(user)
    return client, user


# ----------------------------- CRUD -----------------------------
def test_pm_can_create_link_on_project(pm_client):
    project = ProjectFactory()
    res = pm_client.post("/api/links/",
                         {"url": "https://wiki.example.com/prj", "label": "Confluence",
                          "project": str(project.id)}, format="json")
    assert res.status_code == 201, res.content
    assert res.data["project_name"] == project.name


def test_viewer_cannot_write(viewer_client):
    project = ProjectFactory()
    res = viewer_client.post("/api/links/",
                             {"url": "https://example.com", "project": str(project.id)},
                             format="json")
    assert res.status_code == 403


def test_team_member_can_write(pm_client):
    """Links are as permissive as Task/SubTask: any Team Member may add one."""
    from django.contrib.auth.models import Group

    from apps.core.permissions import ROLE_TEAM
    user = User.objects.create_user(username="dev", password="x")
    user.groups.add(Group.objects.get_or_create(name=ROLE_TEAM)[0])
    client = APIClient()
    client.force_authenticate(user)

    project = ProjectFactory()
    res = client.post("/api/links/", {"url": "https://example.com", "project": str(project.id)},
                      format="json")
    assert res.status_code == 201, res.content


def test_delete_is_soft(pm_client):
    project = ProjectFactory()
    link_id = pm_client.post(
        "/api/links/", {"url": "https://example.com", "project": str(project.id)},
        format="json").data["id"]
    res = pm_client.delete(f"/api/links/{link_id}/")
    assert res.status_code == 204
    # Soft-deleted, not gone: excluded from the default list, but a direct
    # fetch by id still works (e.g. a search result reached before it was
    # archived) and reports is_active=False.
    codes = [l["id"] for l in pm_client.get("/api/links/", {"project": project.id}).data["results"]]
    assert link_id not in codes
    detail = pm_client.get(f"/api/links/{link_id}/")
    assert detail.status_code == 200
    assert detail.data["is_active"] is False


# ----------------------------- Exactly-one-owner -----------------------------
def test_rejects_link_with_no_owner(pm_client):
    res = pm_client.post("/api/links/", {"url": "https://example.com"}, format="json")
    assert res.status_code == 400


def test_rejects_link_with_two_owners(pm_client):
    project = ProjectFactory()
    ticket = TicketFactory()
    res = pm_client.post(
        "/api/links/",
        {"url": "https://example.com", "project": str(project.id), "ticket": str(ticket.id)},
        format="json")
    assert res.status_code == 400


def test_ticket_and_work_item_owners_accepted(pm_client):
    seed_ticket_statuses()
    ticket = TicketFactory()
    work_item = WorkItemFactory()
    res_t = pm_client.post("/api/links/", {"url": "https://example.com/t", "ticket": str(ticket.id)},
                           format="json")
    res_w = pm_client.post("/api/links/",
                           {"url": "https://example.com/w", "work_item": str(work_item.id)},
                           format="json")
    assert res_t.status_code == 201, res_t.content
    assert res_w.status_code == 201, res_w.content


# ----------------------------- Filtering -----------------------------
def test_filters_by_project(pm_client):
    p1, p2 = ProjectFactory(), ProjectFactory()
    pm_client.post("/api/links/", {"url": "https://a.com", "project": str(p1.id)}, format="json")
    pm_client.post("/api/links/", {"url": "https://b.com", "project": str(p2.id)}, format="json")

    res = pm_client.get(f"/api/links/?project={p1.id}")
    assert res.data["count"] == 1
    assert res.data["results"][0]["url"] == "https://a.com"


# ----------------------------- Note isolation -----------------------------
def test_note_link_is_private_to_its_owner():
    alice, _ = _roleless_client("alice")
    bob, _ = _roleless_client("bob")
    note_id = alice.post("/api/notes/", {"title": "Private"}, format="json").data["id"]

    ok = alice.post("/api/links/", {"url": "https://example.com", "note": note_id}, format="json")
    assert ok.status_code == 201, ok.content

    blocked = bob.post("/api/links/", {"url": "https://evil.com", "note": note_id}, format="json")
    assert blocked.status_code == 400

    assert bob.get(f"/api/links/?note={note_id}").data["count"] == 0
    assert alice.get(f"/api/links/?note={note_id}").data["count"] == 1
