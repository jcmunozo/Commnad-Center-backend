from rest_framework import serializers

from .models import Action, Issue, ProjectUpdate, Risk


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ("id", "legacy_code", "project", "api", "date_reported", "reported_by",
                  "reported_by_name", "description", "impact", "urgency", "assignee",
                  "status", "resolution_date", "lessons_learned", "is_active")
        read_only_fields = ("id", "is_active")

    def validate(self, attrs):
        if not attrs.get("reported_by") and not attrs.get("reported_by_name"):
            raise serializers.ValidationError("Provide reported_by (employee) or reported_by_name.")
        return attrs


class RiskSerializer(serializers.ModelSerializer):
    exposure = serializers.IntegerField(read_only=True)
    classification = serializers.CharField(read_only=True)

    class Meta:
        model = Risk
        fields = ("id", "legacy_code", "project", "description", "probability", "impact",
                  "exposure", "classification", "mitigation_plan", "owner_employee",
                  "status", "identified_date", "last_review", "is_active")
        read_only_fields = ("id", "exposure", "classification", "is_active")

    def validate_probability(self, v):
        if not 1 <= v <= 5:
            raise serializers.ValidationError("probability must be 1..5.")
        return v

    def validate_impact(self, v):
        if not 1 <= v <= 5:
            raise serializers.ValidationError("impact must be 1..5.")
        return v


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdate
        fields = ("id", "legacy_code", "project", "api", "update_date", "update_type",
                  "description", "responsible", "action_required", "due_date", "status", "is_active")
        read_only_fields = ("id", "is_active")


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ("id", "legacy_code", "project", "api", "created_date", "origin", "description",
                  "assignee", "due_date", "priority", "impact", "status", "notes", "is_active")
        read_only_fields = ("id", "is_active")
