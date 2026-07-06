from django.db import models


class CatalogBase(models.Model):
    """Reference table base. PK is a stable natural code (Fase 2 decision)."""

    code = models.CharField(primary_key=True, max_length=30)
    name = models.CharField(max_length=100)
    sort_order = models.SmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class SeverityLevel(CatalogBase):
    """Unified Priority / Urgency / Impact scale (Fase 2 #12)."""

    weight = models.SmallIntegerField(default=0)

    class Meta(CatalogBase.Meta):
        db_table = "severity_level"
        verbose_name = "severity level"


class HealthStatus(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "health_status"


class ProjectType(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "project_type"


class ProjectStatus(CatalogBase):
    is_closed = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "project_status"


class TaskStatus(CatalogBase):
    is_closed = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "task_status"


class ApiStatus(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "api_status"


class EndpointStatus(CatalogBase):
    is_done = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "endpoint_status"


class RiskStatus(CatalogBase):
    is_closed = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "risk_status"


class IssueStatus(CatalogBase):
    is_closed = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "issue_status"


class MilestoneStatus(CatalogBase):
    is_closed = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "milestone_status"


class ActionStatus(CatalogBase):
    is_closed = models.BooleanField(default=False)

    class Meta(CatalogBase.Meta):
        db_table = "action_status"


class UpdateType(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "update_type"


class ActionOrigin(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "action_origin"


class TaskType(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "task_type"


class HttpMethod(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "http_method"


class EmployeeLevel(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "employee_level"


class EmployeeStatus(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "employee_status"


class Location(CatalogBase):
    class Meta(CatalogBase.Meta):
        db_table = "location"


class Timezone(CatalogBase):
    utc_offset = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta(CatalogBase.Meta):
        db_table = "timezone"


class Shift(CatalogBase):
    start_hour = models.SmallIntegerField(null=True, blank=True)
    end_hour = models.SmallIntegerField(null=True, blank=True)

    class Meta(CatalogBase.Meta):
        db_table = "shift"
