import uuid

from django.conf import settings
from django.db import models


class ActiveManager(models.Manager):
    """Returns only non-soft-deleted rows (is_active=True)."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class TimeStampedModel(models.Model):
    """Standard audit base for every transactional table (Fase 2).

    Provides UUID PK, created/updated timestamps + authors, and a soft-delete
    flag. Exposes two managers: ``objects`` (all rows) and ``active`` (live rows).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])
