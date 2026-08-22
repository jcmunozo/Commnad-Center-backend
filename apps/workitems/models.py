"""Continuous Improvement: work initiated internally (docs, tech debt, proxy
adjustments) that doesn't fit a delivery Project's phases/health/hitos, but
still needs manual hours + an optional milestone — same shape as
Project/Task/Milestone, one level shallower (no subtasks, Fase X decision).

``WorkItem.project`` is optional: set when the work traces back to an
already-delivered proxy/project, null when it's purely internal (e.g. a
standards doc). Mirrors apps.notes.Note's optional project FK.
"""
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel
from apps.projects.models import PCT


class WorkItem(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey("projects.Project", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="work_items")
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    status = models.ForeignKey("catalogs.ProjectStatus", on_delete=models.PROTECT, related_name="+")
    priority = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")

    history = HistoricalRecords()

    class Meta:
        db_table = "work_item"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["project"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.title}".strip()


class WorkItemTask(TimeStampedModel):
    """Flat task under a WorkItem — no further subtask nesting by design."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    work_item = models.ForeignKey(WorkItem, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=300)
    assignee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="work_item_tasks")
    status = models.ForeignKey("catalogs.TaskStatus", on_delete=models.PROTECT, related_name="+")
    priority = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    progress_pct = models.DecimalField(default=0, **PCT)
    notes = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        db_table = "work_item_task"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["work_item"]),
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class WorkItemMilestone(TimeStampedModel):
    """Optional delivery/handoff marker for a WorkItem (e.g. "docs handed to
    team X") — a WorkItem may have zero, one, or several, added manually like
    a Project's Milestone. Status/progress derived from linked tasks, same
    rule as apps.projects.Milestone (Fase 1 #2)."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    work_item = models.ForeignKey(WorkItem, on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=250)
    owner_employee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name="owned_work_item_milestones")
    target_date = models.DateTimeField(null=True, blank=True)
    actual_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    tasks = models.ManyToManyField(WorkItemTask, through="WorkItemMilestoneTask",
                                   related_name="milestones")

    history = HistoricalRecords()

    class Meta:
        db_table = "work_item_milestone"
        ordering = ["target_date"]
        indexes = [
            models.Index(fields=["target_date"]),
            models.Index(fields=["work_item"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.name}".strip()


class WorkItemMilestoneTask(models.Model):
    id = models.BigAutoField(primary_key=True)
    milestone = models.ForeignKey(WorkItemMilestone, on_delete=models.CASCADE)
    task = models.ForeignKey(WorkItemTask, on_delete=models.CASCADE)

    class Meta:
        db_table = "work_item_milestone_task"
        constraints = [
            models.UniqueConstraint(fields=["milestone", "task"], name="work_item_milestone_task_uq"),
        ]
