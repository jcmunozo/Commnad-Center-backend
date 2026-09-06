from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class Link(TimeStampedModel):
    """External reference URL (Confluence, Swagger, Drive, a design doc…)
    attached to exactly one record — a Project, a Note, a Ticket, or a
    Continuous Improvement work item. Added because each project's
    documentation was scattered across different links with no single place
    to find them; a plain FK per owner (rather than a GenericForeignKey)
    matches how the rest of the app links across apps (see Note.project/
    Note.work_item)."""

    url = models.URLField(max_length=500)
    label = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    project = models.ForeignKey("projects.Project", null=True, blank=True,
                                on_delete=models.CASCADE, related_name="links")
    note = models.ForeignKey("notes.Note", null=True, blank=True,
                             on_delete=models.CASCADE, related_name="links")
    ticket = models.ForeignKey("tickets.Ticket", null=True, blank=True,
                               on_delete=models.CASCADE, related_name="links")
    work_item = models.ForeignKey("workitems.WorkItem", null=True, blank=True,
                                  on_delete=models.CASCADE, related_name="links")

    class Meta:
        db_table = "link"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project"]), models.Index(fields=["note"]),
            models.Index(fields=["ticket"]), models.Index(fields=["work_item"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="link_exactly_one_owner",
                check=(
                    Q(project__isnull=False, note__isnull=True, ticket__isnull=True, work_item__isnull=True)
                    | Q(project__isnull=True, note__isnull=False, ticket__isnull=True, work_item__isnull=True)
                    | Q(project__isnull=True, note__isnull=True, ticket__isnull=False, work_item__isnull=True)
                    | Q(project__isnull=True, note__isnull=True, ticket__isnull=True, work_item__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return self.label or self.url
