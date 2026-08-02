"""Workspace application configuration."""

from django.apps import AppConfig


class WorkspacesConfig(AppConfig):
    """Configure the workspace domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workspaces"
