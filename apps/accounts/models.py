import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class AppUser(AbstractUser):
    """Custom user with a UUID PK.

    Optionally links to a resources.Employee so an authenticated user can be
    mapped to their PMO roster identity (owner/assignee resolution).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        "resources.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_account",
    )

    class Meta:
        db_table = "app_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def role_names(self) -> list[str]:
        return list(self.groups.values_list("name", flat=True))
