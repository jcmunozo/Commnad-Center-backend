from rest_framework import serializers

from .models import Employee, EmployeeShift, TaskAssignment


class EmployeeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ("id", "legacy_code", "name", "role", "level", "status", "location", "timezone")


class EmployeeDetailSerializer(serializers.ModelSerializer):
    capacity_hours = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Employee
        fields = ("id", "legacy_code", "name", "role", "manager", "availability_pct",
                  "weekly_hours", "capacity_hours", "level", "status", "location", "timezone",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "capacity_hours", "is_active", "created_at", "updated_at")


class EmployeeShiftSerializer(serializers.ModelSerializer):
    """Acepta un turno de catálogo (``shift``) o un rango libre
    (``start_hour``/``end_hour``); el rango libre crea/reusa la entrada de
    catálogo H{ss}_{ee} al guardar (ver EmployeeViewSet.schedule)."""

    shift = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeShift._meta.get_field("shift").related_model.objects.all(),
        required=False, allow_null=True)
    start_hour = serializers.IntegerField(required=False, allow_null=True,
                                          min_value=0, max_value=23)
    end_hour = serializers.IntegerField(required=False, allow_null=True,
                                        min_value=0, max_value=23)

    class Meta:
        model = EmployeeShift
        fields = ("id", "employee", "weekday", "shift", "start_hour", "end_hour")
        # El PUT del schedule es full-replace (borra y recrea): el validador
        # de unicidad (employee, weekday) chocaría con las filas por borrar.
        validators = []

    def validate_weekday(self, value):
        if not 1 <= value <= 7:
            raise serializers.ValidationError("weekday must be 1 (Mon) .. 7 (Sun).")
        return value

    def validate(self, attrs):
        has_hours = attrs.get("start_hour") is not None and attrs.get("end_hour") is not None
        if not attrs.get("shift") and not has_hours:
            raise serializers.ValidationError("Provide shift or start_hour+end_hour.")
        if has_hours and attrs["start_hour"] == attrs["end_hour"]:
            raise serializers.ValidationError("start_hour and end_hour must differ.")
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["start_hour"] = instance.shift.start_hour
        data["end_hour"] = instance.shift.end_hour
        data["shift_name"] = instance.shift.name
        return data


class TaskAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    task_name = serializers.CharField(source="task.name", read_only=True)
    task_code = serializers.CharField(source="task.legacy_code", read_only=True, default=None)

    class Meta:
        model = TaskAssignment
        fields = ("id", "legacy_code", "task", "task_name", "task_code", "employee",
                  "employee_name", "assigned_date", "delivery_date", "is_active")
        read_only_fields = ("id", "is_active")


class WorkloadRowSerializer(serializers.Serializer):
    employee_id = serializers.CharField()
    name = serializers.CharField()
    assigned_hours = serializers.FloatField()
    capacity_hours = serializers.FloatField()
    workload_pct = serializers.FloatField()
    alert = serializers.CharField()
    shift_today = serializers.CharField(allow_null=True)
    open_tasks = serializers.IntegerField()
    ticket_hours = serializers.FloatField()
    open_tickets = serializers.IntegerField()
