from rest_framework.routers import DefaultRouter

from .views import ActionViewSet, IssueViewSet, ProjectUpdateViewSet, RiskViewSet

router = DefaultRouter()
router.register("issues", IssueViewSet, basename="issue")
router.register("risks", RiskViewSet, basename="risk")
router.register("updates", ProjectUpdateViewSet, basename="update")
router.register("actions", ActionViewSet, basename="action")

urlpatterns = router.urls
