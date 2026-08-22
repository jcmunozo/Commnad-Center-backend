from rest_framework import serializers

from .models import WorkItem, WorkItemMilestone, WorkItemTask
from .selectors import milestone_progress


# ----------------------------- WorkItem -----------------------------
class WorkItemListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, default=None)
    project_code = serializers.CharField(source="project.legacy_code", read_only=True, default=None)
    status = serializers.CharField(source="status_id", read_only=True)
    priority = serializers.CharField(source="priority_id", read_only=True)
    task_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = WorkItem
        fields = ("id", "legacy_code", "title", "project", "project_name", "project_code",
                  "status", "priority", "task_count", "created_at")


class WorkItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkItem
        fields = ("id", "legacy_code", "title", "description", "project",
                  "status", "priority", "custom_fields", "is_active",
                  "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class WorkItemWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = WorkItem
        fields = ("id", "legacy_code", "title", "description", "project",
                  "status", "priority", "custom_fields")


# ----------------------------- WorkItemTask -----------------------------
class WorkItemTaskListSerializer(serializers.ModelSerializer):
    work_item_title = serializers.CharField(source="work_item.title", read_only=True)
    status = serializers.CharField(source="status_id", read_only=True)
    assignee_name = serializers.CharField(source="assignee.name", read_only=True, default=None)

    class Meta:
        model = WorkItemTask
        fields = ("id", "legacy_code", "name", "work_item", "work_item_title",
                  "assignee", "assignee_name", "status", "priority", "planned_end",
                  "estimated_hours", "progress_pct")


class WorkItemTaskDetailSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source="assignee.name", read_only=True, default=None)

    class Meta:
        model = WorkItemTask
        fields = ("id", "legacy_code", "work_item", "name", "assignee", "assignee_name",
                  "status", "priority", "planned_start", "planned_end", "estimated_hours",
                  "actual_hours", "progress_pct", "notes", "custom_fields", "is_active",
                  "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


class WorkItemTaskWriteSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = WorkItemTask
        fields = ("id", "legacy_code", "work_item", "name", "assignee", "status", "priority",
                  "planned_start", "planned_end", "estimated_hours", "actual_hours",
                  "progress_pct", "notes", "custom_fields")


# ----------------------------- WorkItemMilestone -----------------------------
class WorkItemMilestoneSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source="owner_employee.name", read_only=True, default=None)

    class Meta:
        model = WorkItemMilestone
        fields = ("id", "legacy_code", "work_item", "name", "owner_employee", "owner_name",
                  "target_date", "actual_date", "comments", "progress", "is_active")
        read_only_fields = ("id", "is_active", "progress")

    def get_progress(self, obj):
        return milestone_progress(obj)
