import factory
from factory.django import DjangoModelFactory

from apps.catalogs import models as cat
from apps.projects.models import Project, Task
from apps.resources.models import Employee
from apps.tickets.models import Ticket


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


def employee_status(code="ACTIVE"):
    return cat.EmployeeStatus.objects.get_or_create(code=code, defaults={"name": code})[0]


def ticket_status(code="WIP", is_closed=False):
    return cat.TicketStatus.objects.get_or_create(
        code=code, defaults={"name": code, "is_closed": is_closed})[0]


def seed_ticket_statuses():
    ticket_status("WIP")
    ticket_status("PAUSED")
    ticket_status("RESOLVED", is_closed=True)


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    legacy_code = factory.Sequence(lambda n: f"PRJ-{n:03d}")
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


class EmployeeFactory(DjangoModelFactory):
    class Meta:
        model = Employee

    name = factory.Sequence(lambda n: f"Employee {n}")
    legacy_code = factory.Sequence(lambda n: f"EMP-{n:03d}")
    status = factory.LazyFunction(employee_status)


class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    name = factory.Sequence(lambda n: f"Ticket {n}")
    ticket_number = factory.Sequence(lambda n: f"INC-{n:05d}")
    legacy_code = factory.Sequence(lambda n: f"TCK-{n:03d}")
    priority = factory.LazyFunction(sev)
    status = factory.LazyFunction(ticket_status)
