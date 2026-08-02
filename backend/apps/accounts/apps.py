"""Accounts application configuration."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Authentication and user identities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
