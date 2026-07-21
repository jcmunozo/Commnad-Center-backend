from rest_framework.permissions import IsAuthenticated

from apps.core.views import BaseModelViewSet

from .filters import NoteFilter
from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(BaseModelViewSet):
    """Notas personales: cada usuario gestiona únicamente las suyas."""

    legacy_prefix = "NTE"
    serializer_class = NoteSerializer
    filterset_class = NoteFilter
    search_fields = ["title", "content", "legacy_code"]
    ordering_fields = ["created_at", "due_date", "pinned", "title"]

    def get_permissions(self):
        # A diferencia del base, cualquier autenticado escribe; el aislamiento
        # viene del queryset acotado por created_by.
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:  # generación de schema (drf-spectacular)
            return Note.active.none()
        return Note.active.filter(created_by=user).select_related("project")
