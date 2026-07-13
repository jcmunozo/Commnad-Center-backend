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
        """Group names, plus the implicit admin role superusers get in
        apps.core.permissions.user_in_roles — clients (frontend guards) rely
        on this list matching what the API will actually authorize."""
        from apps.core.permissions import ROLE_ADMIN

        names = list(self.groups.values_list("name", flat=True))
        if self.is_superuser and ROLE_ADMIN not in names:
            names.append(ROLE_ADMIN)
        return names
