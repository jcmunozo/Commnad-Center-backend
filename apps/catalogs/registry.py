"""Central registry mapping URL slugs to catalog models.

Used by serializers, viewsets and urls to expose every catalog under
``/api/catalogs/<slug>/`` without hand-writing 20 near-identical classes.
"""
from . import models

CATALOGS = {
    "severity-levels": models.SeverityLevel,
    "health-statuses": models.HealthStatus,
    "project-types": models.ProjectType,
    "project-statuses": models.ProjectStatus,
    "task-statuses": models.TaskStatus,
    "api-statuses": models.ApiStatus,
    "endpoint-statuses": models.EndpointStatus,
    "risk-statuses": models.RiskStatus,
    "issue-statuses": models.IssueStatus,
    "milestone-statuses": models.MilestoneStatus,
    "action-statuses": models.ActionStatus,
    "update-types": models.UpdateType,
    "action-origins": models.ActionOrigin,
    "task-types": models.TaskType,
    "http-methods": models.HttpMethod,
    "employee-levels": models.EmployeeLevel,
    "employee-statuses": models.EmployeeStatus,
    "locations": models.Location,
    "timezones": models.Timezone,
    "shifts": models.Shift,
}
