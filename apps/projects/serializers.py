from rest_framework import serializers

from .models import (
    ApiComponent,
    Endpoint,
    Milestone,
    Project,
    Task,
    TaskDependency,
)
from .selectors import milestone_progress


# ----------------------------- Project -----------------------------
class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    status = serializers.CharField(source="status_id", read_only=True)
    priority = serializers.CharField(source="priority_id", read_only=True)
    health = serializers.CharField(source="health_id", read_only=True)

    class Meta:
        model = Project
        fields = ("id", "legacy_code", "name", "client_name", "project_type",
                  "status", "priority", "health", "progress_pct", "planned_end")


class ProjectDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = Project
        fields = ("id", "legacy_code", "name", "client", "client_name", "project_type",
                  "status", "priority", "health", "start_date", "planned_end", "actual_end",
                  "progress_pct", "planned_hours", "consumed_hours", "comments",
                  "custom_fields", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("legacy_code", "name", "client", "project_type", "status", "priority",
                  "health", "start_date", "planned_end", "actual_end", "progress_pct",
                  "planned_hours", "consumed_hours", "comments", "custom_fields")

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("planned_end")
        if start and end and end < start:
            raise serializers.ValidationError("planned_end cannot be before start_date.")
        return attrs


# ----------------------------- API / Endpoint -----------------------------
class ApiComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiComponent
        fields = ("id", "legacy_code", "owner_project", "name", "description", "version",
                  "status", "owner_employee", "comments", "is_active")
        read_only_fields = ("id", "is_active")


class EndpointSerializer(serializers.ModelSerializer):
    owner_project = serializers.UUIDField(source="owner_project_id", read_only=True)

    class Meta:
        model = Endpoint
        fields = ("id", "legacy_code", "api", "owner_project", "http_method", "path",
                  "description", "status", "owner_employee", "comments", "is_active")
        read_only_fields = ("id", "owner_project", "is_active")


# ----------------------------- Task -----------------------------
class TaskListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    status = serializers.CharField(source="status_id", read_only=True)

    class Meta:
        model = Task
        fields = ("id", "legacy_code", "name", "project", "project_name", "task_type",
                  "status", "priority", "planned_end", "progress_pct")


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee_ids = serializers.PrimaryKeyRelatedField(source="assignees", many=True, read_only=True)
    blocked_by_ids = serializers.PrimaryKeyRelatedField(source="blocked_by", many=True, read_only=True)

    class Meta:
        model = Task
        fields = ("id", "legacy_code", "name", "project", "api", "endpoint", "task_type",
                  "status", "priority", "planned_start", "planned_end", "estimated_hours",
                  "actual_hours", "progress_pct", "notes", "assignee_ids", "blocked_by_ids",
                  "custom_fields", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class TaskWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("legacy_code", "name", "project", "api", "endpoint", "task_type", "status",
                  "priority", "planned_start", "planned_end", "estimated_hours", "actual_hours",
                  "progress_pct", "notes", "custom_fields")

    def validate(self, attrs):
        api, endpoint = attrs.get("api"), attrs.get("endpoint")
        if endpoint and api and endpoint.api_id != api.id:
            raise serializers.ValidationError("endpoint does not belong to the given api.")
        return attrs


class TaskDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDependency
        fields = ("id", "task", "blocked_by")

    def validate(self, attrs):
        if attrs["task"] == attrs["blocked_by"]:
            raise serializers.ValidationError("A task cannot block itself.")
        return attrs


# ----------------------------- Milestone -----------------------------
class MilestoneSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = ("id", "legacy_code", "project", "api", "name", "owner_employee",
                  "target_date", "actual_date", "comments", "progress", "is_active")
        read_only_fields = ("id", "is_active", "progress")

    def get_progress(self, obj):
        """Derived status/progress from linked tasks (Fase 1 #2)."""
        return milestone_progress(obj)


# ----------------------------- KPI outputs -----------------------------
class DashboardSerializer(serializers.Serializer):
    project_id = serializers.CharField()
    open_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    open_issues = serializers.IntegerField()
    open_risks = serializers.IntegerField()
    critical_risks = serializers.IntegerField()
    total_apis = serializers.IntegerField()
    endpoints_total = serializers.IntegerField()
    endpoints_done = serializers.IntegerField()


class ProgressSerializer(serializers.Serializer):
    project_id = serializers.CharField()
    weighted_progress_pct = serializers.FloatField()
    task_count = serializers.IntegerField()
