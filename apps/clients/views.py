from apps.core.views import BaseModelViewSet

from .filters import ClientFilter
from .serializers import ClientSerializer


class ClientViewSet(BaseModelViewSet):
    """CRUD for clients. Writes limited to PMO Admin / Project Manager."""

    serializer_class = ClientSerializer
    filterset_class = ClientFilter
    search_fields = ["name", "contact_name", "legacy_code"]
    ordering_fields = ["name", "created_at"]
