"""Safe runtime access to centrally governed contact channels."""

from django.conf import settings
from django.db import DatabaseError


def notification_sender_email() -> str:
    """Return the configured sender while remaining safe during migration/recovery."""

    fallback = str(getattr(settings, "DEFAULT_FROM_EMAIL", "hello@crowdsmarter.com")).strip()
    try:
        from .models import PlatformConfiguration

        value = (
            PlatformConfiguration.objects.filter(singleton_key=1)
            .values_list("notification_sender_email", flat=True)
            .first()
        )
    except DatabaseError:
        return fallback
    return str(value or fallback).strip() or fallback
