"""Organisations application configuration."""

from django.apps import AppConfig


class OrganisationsConfig(AppConfig):
    """Tenant and membership domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.organisations"
