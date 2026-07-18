"""Per-user project favorites: toggle endpoint, list annotation, filter, pinning."""
import pytest
from rest_framework.test import APIClient

from apps.projects.models import ProjectFavorite
from tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


def _fav(client, project):
    return client.post(f"/api/projects/{project.id}/favorite/")


def test_toggle_favorite(pm_client):
    project = ProjectFactory()
    res = _fav(pm_client, project)
    assert res.status_code == 200 and res.data["is_favorite"] is True
    assert ProjectFavorite.objects.count() == 1

    res = _fav(pm_client, project)  # second call unstars
    assert res.data["is_favorite"] is False
    assert ProjectFavorite.objects.count() == 0


def test_list_returns_own_favorites_only(pm_client, viewer_user):
    starred, plain = ProjectFactory(), ProjectFactory()
    _fav(pm_client, starred)

    by_id = {r["id"]: r["is_favorite"] for r in pm_client.get("/api/projects/").data["results"]}
    assert by_id[str(starred.id)] is True
    assert by_id[str(plain.id)] is False

    # another user's list is untouched by my stars (fresh client: the shared
    # api_client fixture would re-authenticate the same instance)
    viewer = APIClient()
    viewer.force_authenticate(viewer_user)
    viewer_rows = viewer.get("/api/projects/").data["results"]
    assert all(r["is_favorite"] is False for r in viewer_rows)


def test_favorite_filter_and_pinned_ordering(pm_client):
    a = ProjectFactory(name="AAA plain")
    z = ProjectFactory(name="ZZZ starred")
    _fav(pm_client, z)

    only_fav = pm_client.get("/api/projects/?favorite=true").data["results"]
    assert [r["id"] for r in only_fav] == [str(z.id)]

    pinned = pm_client.get("/api/projects/?ordering=-is_favorite,name").data["results"]
    assert [r["id"] for r in pinned] == [str(z.id), str(a.id)]


def test_viewer_can_favorite(viewer_client):
    """Stars are personal, not a write on the project: any role may use them."""
    project = ProjectFactory()
    assert _fav(viewer_client, project).status_code == 200
