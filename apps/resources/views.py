from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ROLE_ADMIN, ROLE_PM, role_required
from apps.core.views import BaseModelViewSet

from . import services
from .filters import EmployeeFilter, TaskAssignmentFilter
from .models import Employee, EmployeeShift, TaskAssignment
from .serializers import (
    EmployeeDetailSerializer,
    EmployeeListSerializer,
    EmployeeShiftSerializer,
    TaskAssignmentSerializer,
    WorkloadRowSerializer,
)


class EmployeeViewSet(BaseModelViewSet):
    """Employee roster. Writes limited to PMO Admin."""

    write_roles = (ROLE_ADMIN,)
    filterset_class = EmployeeFilter
    search_fields = ["name", "role", "legacy_code"]
    ordering_fields = ["name", "created_at"]
    serializer_class = EmployeeDetailSerializer

    def get_queryset(self):
        return Employee.active.select_related("level", "status", "location", "timezone").all()

    def get_serializer_class(self):
        return EmployeeListSerializer if self.action == "list" else EmployeeDetailSerializer

    @extend_schema(request=EmployeeShiftSerializer(many=True), responses=EmployeeShiftSerializer(many=True))
    @action(detail=True, methods=["get", "put"])
    def schedule(self, request, pk=None):
        """Get or replace the employee's current-week shifts (Mon..Sun)."""
        employee = self.get_object()
        if request.method == "GET":
            qs = EmployeeShift.objects.filter(employee=employee)
            return Response(EmployeeShiftSerializer(qs, many=True).data)

        # PUT: full replace of the week
        serializer = EmployeeShiftSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        EmployeeShift.objects.filter(employee=employee).delete()
        EmployeeShift.objects.bulk_create([
            EmployeeShift(employee=employee, weekday=row["weekday"], shift=row["shift"])
            for row in serializer.validated_data
        ])
        qs = EmployeeShift.objects.filter(employee=employee)
        return Response(EmployeeShiftSerializer(qs, many=True).data)


class TaskAssignmentViewSet(BaseModelViewSet):
    """Assign collaborators to tasks (drives workload)."""

    write_roles = (ROLE_ADMIN, ROLE_PM)
    serializer_class = TaskAssignmentSerializer
    filterset_class = TaskAssignmentFilter
    ordering_fields = ["assigned_date", "created_at"]

    def get_queryset(self):
        return TaskAssignment.active.select_related("task", "employee").all()


class WorkloadView(APIView):
    """Prorated workload per employee over an optional period.

    Query params: ``start`` and ``end`` (ISO datetimes) filter by task window.
    """

    permission_classes = [role_required(ROLE_ADMIN, ROLE_PM)]

    @extend_schema(responses=WorkloadRowSerializer(many=True))
    def get(self, request):
        start = parse_datetime(request.query_params.get("start", "") or "")
        end = parse_datetime(request.query_params.get("end", "") or "")
        data = services.employee_workload(period_start=start, period_end=end)
        return Response(WorkloadRowSerializer(data, many=True).data)
