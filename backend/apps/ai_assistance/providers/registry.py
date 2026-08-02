"""Configuration-driven provider loading."""

from django.conf import settings
from django.utils.module_loading import import_string

from .base import AIProvider


def get_provider() -> AIProvider:
    """Instantiate and validate the configured replaceable provider."""
    provider_class = import_string(settings.AI_PROVIDER_BACKEND)
    provider = provider_class()
    text_attributes = ["key", "label", "model_identifier"]
    for attribute in text_attributes:
        value = getattr(provider, attribute, None)
        if not isinstance(value, str) or not value.strip():
            raise TypeError(
                f"Configured AI provider requires a non-empty '{attribute}' string."
            )
    if not callable(getattr(provider, "review_decision", None)):
        raise TypeError(
            "Configured AI provider requires a callable 'review_decision' method."
        )
    return provider
