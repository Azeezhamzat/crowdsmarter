"""Participant application configuration."""

from django.apps import AppConfig


class ParticipantsConfig(AppConfig):
    """Configure the participant domain."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.participants"
