from import_export import fields, resources

from .models import Client


class ClientResource(resources.ModelResource):
    """django-import-export resource. Uses legacy_code as the stable import key."""

    class Meta:
        model = Client
        import_id_fields = ("legacy_code",)
        fields = ("legacy_code", "name", "contact_name", "contact_email", "notes")
        skip_unchanged = True
        report_skipped = True
