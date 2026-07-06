import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, ROLE_VIEWER

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def _user_with_role(role):
    user = User.objects.create_user(username=f"user_{role}".replace(" ", "_"), password="x")
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


@pytest.fixture
def pm_user(db):
    return _user_with_role(ROLE_PM)


@pytest.fixture
def viewer_user(db):
    return _user_with_role(ROLE_VIEWER)


@pytest.fixture
def admin_user(db):
    return _user_with_role(ROLE_ADMIN)


@pytest.fixture
def pm_client(api_client, pm_user):
    api_client.force_authenticate(pm_user)
    return api_client


@pytest.fixture
def viewer_client(api_client, viewer_user):
    api_client.force_authenticate(viewer_user)
    return api_client
