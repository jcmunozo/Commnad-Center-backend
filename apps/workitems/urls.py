from rest_framework.routers import DefaultRouter

from .views import WorkItemMilestoneViewSet, WorkItemTaskViewSet, WorkItemViewSet

router = DefaultRouter()
router.register("work-items", WorkItemViewSet, basename="workitem")
router.register("work-item-tasks", WorkItemTaskViewSet, basename="workitemtask")
router.register("work-item-milestones", WorkItemMilestoneViewSet, basename="workitemmilestone")

urlpatterns = router.urls
