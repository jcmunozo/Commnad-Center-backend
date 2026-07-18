from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class Employee(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=150, blank=True)
    manager = models.ForeignKey("self", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="reports")
    availability_pct = models.DecimalField(
        max_digits=5, decimal_places=4, default=1,
        validators=[MinValueValidator(0), MaxValueValidator(1)])
    weekly_hours = models.DecimalField(max_digits=6, decimal_places=2, default=40)
    level = models.ForeignKey("catalogs.EmployeeLevel", null=True, blank=True,
                              on_delete=models.PROTECT, related_name="+")
    status = models.ForeignKey("catalogs.EmployeeStatus", on_delete=models.PROTECT, related_name="+")
    location = models.ForeignKey("catalogs.Location", null=True, blank=True,
                                 on_delete=models.PROTECT, related_name="+")
    timezone = models.ForeignKey("catalogs.Timezone", null=True, blank=True,
                                 on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "employee"
        ordering = ["name"]
        indexes = [models.Index(fields=["manager"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()

    @property
    def capacity_hours(self):
        return self.weekly_hours * self.availability_pct


class EmployeeShift(models.Model):
    """Current-week shift per employee-day (Fase 1 #6: no history)."""

    id = models.BigAutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="shifts")
    weekday = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)])  # ISO: 1=Mon
    shift = models.ForeignKey("catalogs.Shift", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "employee_shift"
        ordering = ["employee", "weekday"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "weekday"], name="employee_shift_uq"),
        ]


class Leave(TimeStampedModel):
    """Absence window (vacation, sick day, appointment...). Informational —
    no approval workflow: registering it is enough (mirrors the old shared
    Excel). Dates are inclusive; capacity math derives from these rows."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="leaves")
    leave_type = models.ForeignKey("catalogs.LeaveType", on_delete=models.PROTECT, related_name="+")
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "leave"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["employee"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")),
                name="leave_dates_ordered"),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.employee_id} {self.start_date}..{self.end_date}".strip()


class Holiday(TimeStampedModel):
    """Public holiday for one country (a ``Location``): everyone based there
    is off that day. Registered by hand per month/country — no per-employee
    rows, unlike ``Leave``."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    name = models.CharField(max_length=150)
    location = models.ForeignKey("catalogs.Location", on_delete=models.PROTECT, related_name="+")
    date = models.DateField()

    class Meta:
        db_table = "holiday"
        ordering = ["date", "location_id"]
        indexes = [models.Index(fields=["date"])]
        constraints = [
            models.UniqueConstraint(
                fields=["date", "location"], condition=models.Q(is_active=True),
                name="holiday_date_location_uq"),
        ]

    def __str__(self):
        return f"{self.date} {self.name} ({self.location_id})"


class TaskAssignment(TimeStampedModel):
    """Links a task to a collaborator (N:M). Carries no hours: effort lives on
    the task (Fase 1 #10). Workload is prorated among a task's collaborators."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    task = models.ForeignKey("projects.Task", on_delete=models.CASCADE, related_name="assignments")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="assignments")
    assigned_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "task_assignment"
        constraints = [
            models.UniqueConstraint(fields=["task", "employee"], name="task_assignment_uq"),
        ]

    def __str__(self):
        return f"{self.task_id} -> {self.employee_id}"
