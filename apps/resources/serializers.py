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
    class Meta:
        model = EmployeeShift
        fields = ("id", "employee", "weekday", "shift")

    def validate_weekday(self, value):
        if not 1 <= value <= 7:
            raise serializers.ValidationError("weekday must be 1 (Mon) .. 7 (Sun).")
        return value


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
