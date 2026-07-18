from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import (
    ROLE_ADMIN,
    ROLE_PM,
    ROLE_TEAM,
    role_required,
    user_in_roles,
)
from apps.core.views import BaseModelViewSet

from . import services
from .filters import EmployeeFilter, HolidayFilter, LeaveFilter, TaskAssignmentFilter
from .models import Employee, EmployeeShift, Holiday, Leave, TaskAssignment
from .serializers import (
    EmployeeDetailSerializer,
    EmployeeListSerializer,
    EmployeeShiftSerializer,
    HolidaySerializer,
    LeaveCalendarDaySerializer,
    LeaveSerializer,
    TaskAssignmentSerializer,
    WorkloadRowSerializer,
)


class EmployeeViewSet(BaseModelViewSet):
    """Employee roster. Writes limited to PMO Admin."""

    legacy_prefix = "EMP"
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
            EmployeeShift(employee=employee, weekday=row["weekday"],
                          shift=row.get("shift") or _shift_for_hours(
                              row["start_hour"], row["end_hour"]))
            for row in serializer.validated_data
        ])
        qs = EmployeeShift.objects.filter(employee=employee)
        return Response(EmployeeShiftSerializer(qs, many=True).data)


class TaskAssignmentViewSet(BaseModelViewSet):
    """Assign collaborators to tasks (drives workload)."""

    legacy_prefix = "ASG"
    write_roles = (ROLE_ADMIN, ROLE_PM)
    serializer_class = TaskAssignmentSerializer
    filterset_class = TaskAssignmentFilter
    ordering_fields = ["assigned_date", "created_at"]

    def get_queryset(self):
        return TaskAssignment.active.select_related("task", "employee").all()


class LeaveViewSet(BaseModelViewSet):
    """Absence registry (vacation, sick days...). Informational: any team
    member registers their own dates; PMO Admin / PM manage anyone's."""

    legacy_prefix = "LVE"
    write_roles = (ROLE_ADMIN, ROLE_PM, ROLE_TEAM)
    serializer_class = LeaveSerializer
    filterset_class = LeaveFilter
    search_fields = ["employee__name", "notes", "legacy_code"]
    ordering_fields = ["start_date", "end_date", "created_at"]

    def get_queryset(self):
        return Leave.active.select_related("employee", "leave_type").all()

    def _check_ownership(self, employee):
        """Team Members may only touch leaves of their linked employee."""
        user = self.request.user
        if user_in_roles(user, (ROLE_ADMIN, ROLE_PM)):
            return
        own = getattr(user, "employee_id", None)
        if own is None or employee.pk != own:
            raise PermissionDenied("You can only manage your own leaves.")

    def perform_create(self, serializer):
        self._check_ownership(serializer.validated_data["employee"])
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._check_ownership(serializer.instance.employee)
        new_employee = serializer.validated_data.get("employee")
        if new_employee is not None:
            self._check_ownership(new_employee)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        self._check_ownership(instance.employee)
        super().perform_destroy(instance)


class HolidayViewSet(BaseModelViewSet):
    """Country public holidays, registered by hand per month. A holiday takes
    the whole Location's roster out of that day's capacity, so writes stay
    with Admin/PM — unlike personal leaves."""

    legacy_prefix = "HOL"
    write_roles = (ROLE_ADMIN, ROLE_PM)
    serializer_class = HolidaySerializer
    filterset_class = HolidayFilter
    search_fields = ["name", "legacy_code", "location__name"]
    ordering_fields = ["date", "created_at"]

    def get_queryset(self):
        return Holiday.active.select_related("location").all()


class LeaveCalendarView(APIView):
    """Per-day absence counts for capacity checks.

    Query params: ``start`` / ``end`` (ISO dates, default: current month) and
    optional ``threshold`` (0..1) overriding ``settings.LEAVE_ALERT_PCT``.
    Readable by any authenticated user: the whole team plans around it.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter("start", str, description="ISO date (default: first day of current month)"),
            OpenApiParameter("end", str, description="ISO date (default: last day of current month)"),
            OpenApiParameter("threshold", float, description="Alert threshold 0..1 (default: LEAVE_ALERT_PCT)"),
        ],
        responses=LeaveCalendarDaySerializer(many=True),
    )
    def get(self, request):
        today = timezone.localdate()
        start = parse_date(request.query_params.get("start", "") or "") or today.replace(day=1)
        default_end = (start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        end = parse_date(request.query_params.get("end", "") or "") or default_end
        threshold = None
        raw = request.query_params.get("threshold")
        if raw:
            try:
                threshold = float(raw)
            except ValueError:
                raise ValidationError({"threshold": "Must be a number between 0 and 1."}) from None
        try:
            data = services.leave_calendar(start, end, threshold)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(LeaveCalendarDaySerializer(data, many=True).data)


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


def _shift_for_hours(start: int, end: int):
    """Catalog shift for a free hour range; created if missing (H07_16)."""
    from apps.catalogs.models import Shift

    shift, _ = Shift.objects.get_or_create(
        code=f"H{start:02d}_{end:02d}",
        defaults={"name": f"{start:02d}:00 – {end:02d}:00",
                  "start_hour": start, "end_hour": end, "sort_order": 99})
    return shift
