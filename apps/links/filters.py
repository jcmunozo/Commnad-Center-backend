from django_filters import rest_framework as filters

from .models import Link


class LinkFilter(filters.FilterSet):
    class Meta:
        model = Link
        fields = ["project", "note", "ticket", "work_item", "is_active"]
