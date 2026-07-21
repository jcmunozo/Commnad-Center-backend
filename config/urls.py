from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # --- Auth ---
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # --- Apps ---
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.catalogs.urls")),
    path("api/", include("apps.clients.urls")),
    path("api/", include("apps.projects.urls")),
    path("api/", include("apps.resources.urls")),
    path("api/", include("apps.tickets.urls")),
    path("api/", include("apps.notes.urls")),
    # --- Schema ---
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
