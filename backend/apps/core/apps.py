"""Core application configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared infrastructure primitives."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self) -> None:
        from . import checks  # noqa: F401
