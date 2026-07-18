from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    EmployeeViewSet,
    HolidayViewSet,
    LeaveCalendarView,
    LeaveViewSet,
    TaskAssignmentViewSet,
    WorkloadView,
)

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")
router.register("assignments", TaskAssignmentViewSet, basename="assignment")
router.register("leaves", LeaveViewSet, basename="leave")
router.register("holidays", HolidayViewSet, basename="holiday")

urlpatterns = [
    path("resources/workload/", WorkloadView.as_view(), name="resource-workload"),
    path("resources/leave-calendar/", LeaveCalendarView.as_view(), name="leave-calendar"),
    *router.urls,
]
