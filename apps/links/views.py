from django.db.models import Q

from apps.core.permissions import ROLE_ADMIN
from apps.core.views import BaseModelViewSet

from .filters import LinkFilter
from .models import Link
from .permissions import LinkPermission
from .serializers import LinkSerializer


class LinkViewSet(BaseModelViewSet):
    """CRUD for reference links (Confluence, Swagger, Drive…) attached to a
    Project, Note, Ticket, or Continuous Improvement work item — one shared
    endpoint, filtered by owner (``?project=``/``note=``/``ticket=``/
    ``work_item=``). Write access is as permissive as Task/SubTask (any
    Team Member) since a link is just metadata, not the owning record
    itself — except a link on a Note, which (like the note itself) stays
    open to its own creator regardless of role; see :mod:`.permissions`."""

    serializer_class = LinkSerializer
    filterset_class = LinkFilter
    search_fields = ["label", "url"]
    ordering_fields = ["created_at", "label"]

    def get_permissions(self):
        return [LinkPermission()]

    def get_queryset(self):
        qs = Link.active.select_related("project", "note", "ticket", "work_item")
        user = self.request.user
        if not (user.is_authenticated and
                (user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists())):
            # A note is personal (isolated by created_by everywhere else in
            # the app) — don't let its links leak through this shared endpoint.
            qs = qs.filter(Q(note__isnull=True) | Q(note__created_by=user))
        return qs
