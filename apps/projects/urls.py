from django.urls import path
from rest_framework.routers import DefaultRouter

from .dashboards import AlertsView, PortfolioDashboardView
from .views import (
    MilestoneViewSet,
    ProjectViewSet,
    SubTaskViewSet,
    TaskViewSet,
)

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")
router.register("subtasks", SubTaskViewSet, basename="subtask")
router.register("milestones", MilestoneViewSet, basename="milestone")

urlpatterns = [
    path("dashboard/portfolio/", PortfolioDashboardView.as_view(), name="portfolio-dashboard"),
    path("dashboard/alerts/", AlertsView.as_view(), name="portfolio-alerts"),
    *router.urls,
]
