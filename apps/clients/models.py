from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel


class Client(TimeStampedModel):
    """PMO client. Lightweight per Fase 1 #4 (name + basic contact data)."""

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200, unique=True)
    contact_name = models.CharField(max_length=200, blank=True)   # propuesto
    contact_email = models.EmailField(blank=True)                 # propuesto
    notes = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        db_table = "client"
        ordering = ["name"]
        verbose_name = "client"
        verbose_name_plural = "clients"

    def __str__(self):
        return self.name
