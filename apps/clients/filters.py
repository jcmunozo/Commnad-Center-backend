from django_filters import rest_framework as filters

from .models import Client


class ClientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Client
        fields = ["name", "is_active"]
