"""User account model."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from .managers import UserManager


class User(AbstractUser):
    """A user identified by email instead of a public username."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="unique_user_email_ci")
        ]

    def clean(self) -> None:
        """Normalise identity fields before validation and persistence."""
        super().clean()
        self.email = self.email.strip().lower()

    def __str__(self) -> str:
        return self.email
