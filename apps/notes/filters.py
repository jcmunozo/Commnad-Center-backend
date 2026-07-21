from django_filters import rest_framework as filters

from .models import Note


class NoteFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr="icontains")
    due_before = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    due_after = filters.DateFilter(field_name="due_date", lookup_expr="gte")

    class Meta:
        model = Note
        fields = ["status", "category", "priority", "pinned", "project"]
