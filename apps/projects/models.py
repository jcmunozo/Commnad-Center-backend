from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel

PCT = dict(max_digits=5, decimal_places=4,
           validators=[MinValueValidator(0), MaxValueValidator(1)])


class Project(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project_type = models.ForeignKey("catalogs.ProjectType", on_delete=models.PROTECT)  # propuesto
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    target_name = models.CharField(max_length=200, blank=True)
    trigger_name = models.CharField(max_length=200, blank=True)
    status = models.ForeignKey("catalogs.ProjectStatus", on_delete=models.PROTECT, related_name="+")
    priority = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    health = models.ForeignKey("catalogs.HealthStatus", null=True, blank=True,
                               on_delete=models.PROTECT, related_name="+")
    start_date = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    progress_pct = models.DecimalField(default=0, **PCT)
    planned_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    consumed_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comments = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        db_table = "project"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["planned_end"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class ProjectPhase(models.Model):
    """Timeline entry for a project's delivery phase (Dev → Hypercare).

    One row per (project, phase); the full set is replaced via the
    ``/projects/{id}/phases/`` action, mirroring the employee schedule PUT.
    """

    PHASES = [
        ("DEV", "Development"),
        ("SIT", "SIT"),
        ("UAT", "UAT"),
        ("PROD", "Production"),
        ("HYPERCARE", "Hypercare"),
    ]

    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="phases")
    phase = models.CharField(max_length=20, choices=PHASES)
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "project_phase"
        ordering = ["project", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "phase"], name="project_phase_uq"),
        ]

    def __str__(self):
        return f"{self.project_id} {self.phase}"


class Task(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    task_type = models.ForeignKey("catalogs.TaskType", on_delete=models.PROTECT, related_name="+")
    name = models.CharField(max_length=300)
    status = models.ForeignKey("catalogs.TaskStatus", on_delete=models.PROTECT, related_name="+")
    priority = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    progress_pct = models.DecimalField(default=0, **PCT)
    notes = models.TextField(blank=True)
    # "blocked by" self relation (Fase 1 #8)
    blocked_by = models.ManyToManyField("self", through="TaskDependency",
                                        symmetrical=False, related_name="blocks")
    assignees = models.ManyToManyField("resources.Employee", through="resources.TaskAssignment",
                                       related_name="tasks")

    history = HistoricalRecords()

    class Meta:
        db_table = "task"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["status"]),
            models.Index(fields=["planned_start", "planned_end"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class TaskDependency(models.Model):
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dep_out")
    blocked_by = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dep_in")

    class Meta:
        db_table = "task_dependency"
        constraints = [
            models.UniqueConstraint(fields=["task", "blocked_by"], name="task_dep_uq"),
            models.CheckConstraint(check=~models.Q(task=models.F("blocked_by")), name="task_dep_no_self"),
        ]


class Milestone(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=250)
    owner_employee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="owned_milestones")
    target_date = models.DateTimeField(null=True, blank=True)
    actual_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    tasks = models.ManyToManyField(Task, through="MilestoneTask", related_name="milestones")

    history = HistoricalRecords()

    class Meta:
        db_table = "milestone"
        ordering = ["target_date"]
        indexes = [models.Index(fields=["target_date"])]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class MilestoneTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    class Meta:
        db_table = "milestone_task"
        constraints = [models.UniqueConstraint(fields=["milestone", "task"], name="milestone_task_uq")]


class SubTask(TimeStampedModel):
    """Pendiente derivado de una tarea: deuda o recordatorio puntual (reemplaza
    a los antiguos riesgos/incidencias/acciones/bitácora, 2026-07-14)."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    description = models.TextField()
    assignee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="subtasks")
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.ForeignKey("catalogs.SeverityLevel", null=True, blank=True,
                                 on_delete=models.PROTECT, related_name="+")
    status = models.ForeignKey("catalogs.ActionStatus", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "subtask"
        ordering = ["due_date", "-created_at"]
        indexes = [models.Index(fields=["task"]), models.Index(fields=["status"]),
                   models.Index(fields=["assignee"])]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.description[:40]}".strip()
