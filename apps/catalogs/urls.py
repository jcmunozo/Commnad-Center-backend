from rest_framework.routers import DefaultRouter

from .registry import CATALOGS
from .views import build_catalog_viewset

router = DefaultRouter()
for slug, model in CATALOGS.items():
    router.register(f"catalogs/{slug}", build_catalog_viewset(model), basename=slug)

urlpatterns = router.urls
