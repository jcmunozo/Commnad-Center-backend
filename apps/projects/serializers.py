from rest_framework import serializers

from .models import (
    Milestone,
    Project,
    ProjectPhase,
    SubTask,
    Task,
    TaskDependency,
)
from .selectors import milestone_progress


# ----------------------------- Project -----------------------------
class ProjectListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="status_id", read_only=True)
    priority = serializers.CharField(source="priority_id", read_only=True)
    health = serializers.CharField(source="health_id", read_only=True)
    is_favorite = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Project
        fields = ("id", "legacy_code", "name", "project_type",
                  "status", "priority", "health", "progress_pct", "planned_end",
                  "trigger_name", "target_name", "is_favorite")


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = ("phase", "planned_start", "planned_end")


class ProjectDetailSerializer(serializers.ModelSerializer):
    phases = ProjectPhaseSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ("id", "legacy_code", "name", "description", "target_name", "trigger_name",
                  "project_type",
                  "status", "priority", "health", "start_date", "planned_end", "actual_end",
                  "progress_pct", "planned_hours", "consumed_hours", "comments", "phases",
                  "custom_fields", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class ProjectWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Project
        fields = ("id", "legacy_code", "name", "description", "target_name", "trigger_name",
                  "project_type", "status", "priority",
                  "health", "start_date", "planned_end", "actual_end", "progress_pct",
                  "planned_hours", "consumed_hours", "comments", "custom_fields")

    def validate(self, attrs):
        start, end = attrs.get("start_date"), attrs.get("planned_end")
        if start and end and end < start:
            raise serializers.ValidationError("planned_end cannot be before start_date.")
        return attrs


# ----------------------------- Task -----------------------------
class TaskListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    status = serializers.CharField(source="status_id", read_only=True)
    assignees = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ("id", "legacy_code", "name", "project", "project_name", "task_type",
                  "status", "priority", "planned_end", "progress_pct", "assignees")

    def get_assignees(self, obj):
        # Solo asignaciones activas: la M2M cruda incluye filas soft-borradas.
        # ``active_assignments`` viene del Prefetch del viewset; fallback por si
        # se serializa fuera de esa queryset.
        assignments = getattr(obj, "active_assignments", None)
        if assignments is None:
            assignments = obj.assignments.filter(is_active=True).select_related("employee")
        return [{"id": str(a.employee_id), "name": a.employee.name} for a in assignments]


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee_ids = serializers.PrimaryKeyRelatedField(source="assignees", many=True, read_only=True)
    blocked_by_ids = serializers.PrimaryKeyRelatedField(source="blocked_by", many=True, read_only=True)

    class Meta:
        model = Task
        fields = ("id", "legacy_code", "name", "project", "task_type",
                  "status", "priority", "planned_start", "planned_end", "estimated_hours",
                  "actual_hours", "progress_pct", "notes", "assignee_ids", "blocked_by_ids",
                  "custom_fields", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class TaskWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Task
        fields = ("id", "legacy_code", "name", "project", "task_type", "status",
                  "priority", "planned_start", "planned_end", "estimated_hours", "actual_hours",
                  "progress_pct", "notes", "custom_fields")


class TaskDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDependency
        fields = ("id", "task", "blocked_by")

    def validate(self, attrs):
        if attrs["task"] == attrs["blocked_by"]:
            raise serializers.ValidationError("A task cannot block itself.")
        return attrs


class SubTaskSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source="task.name", read_only=True)
    task_code = serializers.CharField(source="task.legacy_code", read_only=True, default=None)
    assignee_name = serializers.CharField(source="assignee.name", read_only=True, default=None)

    class Meta:
        model = SubTask
        fields = ("id", "legacy_code", "task", "task_name", "task_code", "description",
                  "assignee", "assignee_name", "due_date", "priority", "status", "is_active")
        read_only_fields = ("id", "is_active")


# ----------------------------- Milestone -----------------------------
class MilestoneSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = ("id", "legacy_code", "project", "name", "owner_employee",
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
    open_subtasks = serializers.IntegerField()
    overdue_subtasks = serializers.IntegerField()


class ProgressSerializer(serializers.Serializer):
    project_id = serializers.CharField()
    weighted_progress_pct = serializers.FloatField()
    task_count = serializers.IntegerField()
