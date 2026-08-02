"""Demo-request application configuration."""

from django.apps import AppConfig


class DemoRequestsConfig(AppConfig):
    """Public demo-request capture boundary."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.demo_requests"
