from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel


class Issue(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="issues")
    api = models.ForeignKey("projects.ApiComponent", null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="issues")
    date_reported = models.DateTimeField()
    reported_by = models.ForeignKey("resources.Employee", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="reported_issues")
    reported_by_name = models.CharField(max_length=200, blank=True)  # propuesto (external reporter)
    description = models.TextField()
    impact = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    urgency = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    assignee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="assigned_issues")
    status = models.ForeignKey("catalogs.IssueStatus", on_delete=models.PROTECT, related_name="+")
    resolution_date = models.DateTimeField(null=True, blank=True)
    lessons_learned = models.TextField(blank=True)

    class Meta:
        db_table = "issue"
        ordering = ["-date_reported"]
        indexes = [models.Index(fields=["project"]), models.Index(fields=["status"]),
                   models.Index(fields=["assignee"])]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.description[:40]}".strip()


class Risk(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="risks")
    description = models.TextField()
    probability = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    impact = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    exposure = models.GeneratedField(
        expression=models.F("probability") * models.F("impact"),
        output_field=models.SmallIntegerField(),
        db_persist=True,
    )
    mitigation_plan = models.TextField(blank=True)
    owner_employee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="owned_risks")
    status = models.ForeignKey("catalogs.RiskStatus", on_delete=models.PROTECT, related_name="+")
    identified_date = models.DateTimeField(null=True, blank=True)
    last_review = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        db_table = "risk"
        ordering = ["-exposure"]
        indexes = [models.Index(fields=["project"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.legacy_code or ''} (exp={self.exposure})".strip()

    @property
    def classification(self) -> str:
        e = self.exposure or 0
        if e >= 16:
            return "Critical"
        if e >= 9:
            return "High"
        if e >= 4:
            return "Medium"
        return "Low"


class ProjectUpdate(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="updates")
    api = models.ForeignKey("projects.ApiComponent", null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="updates")
    update_date = models.DateTimeField()
    update_type = models.ForeignKey("catalogs.UpdateType", on_delete=models.PROTECT, related_name="+")
    description = models.TextField()
    responsible = models.ForeignKey("resources.Employee", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="updates")
    action_required = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.ForeignKey("catalogs.ActionStatus", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "project_update"
        ordering = ["-update_date"]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.description[:40]}".strip()


class Action(TimeStampedModel):
    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="actions")
    api = models.ForeignKey("projects.ApiComponent", null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="actions")
    created_date = models.DateTimeField()
    origin = models.ForeignKey("catalogs.ActionOrigin", on_delete=models.PROTECT, related_name="+")
    description = models.TextField()
    assignee = models.ForeignKey("resources.Employee", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="assigned_actions")
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.ForeignKey("catalogs.SeverityLevel", on_delete=models.PROTECT, related_name="+")
    impact = models.ForeignKey("catalogs.SeverityLevel", null=True, blank=True,
                               on_delete=models.PROTECT, related_name="+")
    status = models.ForeignKey("catalogs.ActionStatus", on_delete=models.PROTECT, related_name="+")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "action"
        ordering = ["due_date"]
        indexes = [models.Index(fields=["assignee"]), models.Index(fields=["status"]),
                   models.Index(fields=["due_date"])]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.description[:40]}".strip()
