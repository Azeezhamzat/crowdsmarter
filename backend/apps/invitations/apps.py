"""Django application configuration for organisation invitations."""

from django.apps import AppConfig


class InvitationsConfig(AppConfig):
    """Register the invitation domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.invitations"
    verbose_name = "Organisation invitations"
