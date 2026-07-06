from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, TaskAssignmentViewSet, WorkloadView

router = DefaultRouter()
router.register("employees", EmployeeViewSet, basename="employee")
router.register("assignments", TaskAssignmentViewSet, basename="assignment")

urlpatterns = [
    path("resources/workload/", WorkloadView.as_view(), name="resource-workload"),
    *router.urls,
]
