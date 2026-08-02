"""Audit application configuration."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Append-only audit trail."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
