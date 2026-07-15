from django_filters import rest_framework as filters

from .models import Ticket
from .services import RESOLVED


class TicketFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    open = filters.BooleanFilter(method="filter_open")

    class Meta:
        model = Ticket
        fields = ["status", "priority", "assignee", "is_active"]

    def filter_open(self, queryset, name, value):
        if value:
            return queryset.exclude(status_id=RESOLVED)
        return queryset
