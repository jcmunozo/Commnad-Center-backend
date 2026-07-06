import factory
from factory.django import DjangoModelFactory

from apps.catalogs import models as cat
from apps.clients.models import Client
from apps.projects.models import Project, Task


# --- catalog helpers (idempotent get_or_create) ---
def sev(code="HIGH", name="High", weight=3):
    return cat.SeverityLevel.objects.get_or_create(
        code=code, defaults={"name": name, "weight": weight})[0]


def project_status(code="IN_PROGRESS"):
    return cat.ProjectStatus.objects.get_or_create(code=code, defaults={"name": code})[0]


def project_type(code="API"):
    return cat.ProjectType.objects.get_or_create(code=code, defaults={"name": code})[0]


def task_status(code="IN_PROGRESS", is_closed=False):
    return cat.TaskStatus.objects.get_or_create(
        code=code, defaults={"name": code, "is_closed": is_closed})[0]


def task_type(code="DEV"):
    return cat.TaskType.objects.get_or_create(code=code, defaults={"name": code})[0]


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Client {n}")


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    legacy_code = factory.Sequence(lambda n: f"PRJ-{n:03d}")
    client = factory.SubFactory(ClientFactory)
    project_type = factory.LazyFunction(project_type)
    status = factory.LazyFunction(project_status)
    priority = factory.LazyFunction(sev)


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    name = factory.Sequence(lambda n: f"Task {n}")
    legacy_code = factory.Sequence(lambda n: f"TSK-{n:03d}")
    project = factory.SubFactory(ProjectFactory)
    task_type = factory.LazyFunction(task_type)
    status = factory.LazyFunction(task_status)
    priority = factory.LazyFunction(sev)
