from django.db import models

from apps.core.models import TimeStampedModel


class Note(TimeStampedModel):
    """Nota personal ("cosas a tener en mente"). Cada usuario ve solo sus
    propias filas: el viewset acota el queryset por ``created_by``."""

    class Category(models.TextChoices):
        IDEA = "IDEA", "Idea"
        TODO = "TODO", "To-Do"
        REMINDER = "REMINDER", "Reminder"
        DECISION = "DECISION", "Decision"

    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        COMPLETED = "COMPLETED", "Completed"

    legacy_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    title = models.CharField(max_length=250)
    content = models.TextField(blank=True)
    pinned = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    project = models.ForeignKey("projects.Project", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="notes")

    class Meta:
        db_table = "note"
        ordering = ["-pinned", "-created_at"]
        indexes = [
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["created_by", "pinned"]),
        ]

    def __str__(self):
        return f"{self.legacy_code or ''} {self.title}".strip()
