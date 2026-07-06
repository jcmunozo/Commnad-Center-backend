from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel

PCT = dict(max_digits=5, decimal_places=4,
           validators=[MinValueValidator(0), MaxValueValidator(1)])


class Project(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="projects")
    project_type = models.ForeignKey("catalogs.ProjectType", on_delete=models.PROTECT)  # propuesto
    name = models.CharField(max_length=250)
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
            models.Index(fields=["client"]),
            models.Index(fields=["planned_end"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class ApiComponent(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    owner_project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="owned_apis")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=30, blank=True)
    status = models.ForeignKey("catalogs.ApiStatus", on_delete=models.PROTECT, related_name="+")
    owner_employee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="owned_apis")
    comments = models.TextField(blank=True)
    # Reuse across projects (Fase 2 #11): referenced (non-owner) projects.
    reused_in = models.ManyToManyField(Project, through="ProjectApiRef", related_name="referenced_apis")

    class Meta:
        db_table = "api_component"
        ordering = ["name"]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class Endpoint(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    api = models.ForeignKey(ApiComponent, on_delete=models.CASCADE, related_name="endpoints")
    # owner_project derived via api.owner_project (Fase 2 revision: no redundant FK).
    http_method = models.ForeignKey("catalogs.HttpMethod", on_delete=models.PROTECT, related_name="+")
    path = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.ForeignKey("catalogs.EndpointStatus", on_delete=models.PROTECT, related_name="+")
    owner_employee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="owned_endpoints")
    comments = models.TextField(blank=True)
    reused_in = models.ManyToManyField(Project, through="ProjectEndpointRef",
                                       related_name="referenced_endpoints")

    class Meta:
        db_table = "endpoint"
        ordering = ["path"]
        constraints = [
            models.UniqueConstraint(fields=["api", "http_method", "path"], name="endpoint_api_path_uq"),
        ]

    def __str__(self):
        return f"{self.http_method_id} {self.path}"

    @property
    def owner_project_id(self):
        return self.api.owner_project_id


class ProjectApiRef(models.Model):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    api = models.ForeignKey(ApiComponent, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_api_ref"
        constraints = [models.UniqueConstraint(fields=["project", "api"], name="project_api_ref_uq")]


class ProjectEndpointRef(models.Model):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_endpoint_ref"
        constraints = [
            models.UniqueConstraint(fields=["project", "endpoint"], name="project_endpoint_ref_uq"),
        ]


class Task(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    api = models.ForeignKey(ApiComponent, null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="tasks")
    endpoint = models.ForeignKey(Endpoint, null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="tasks")
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
    api = models.ForeignKey(ApiComponent, null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="milestones")
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
