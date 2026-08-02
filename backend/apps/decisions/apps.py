"""Decision application configuration."""

from django.apps import AppConfig


class DecisionsConfig(AppConfig):
    """Configure the decision domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.decisions"
