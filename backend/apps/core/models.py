"""Shared model primitives."""

import uuid

from django.db import models


class UUIDTimeStampedModel(models.Model):
    """Abstract model with UUID identity and immutable creation timestamp."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
