"""Configuration-driven provider loading."""

from django.conf import settings
from django.utils.module_loading import import_string

from .base import AIProvider

PROVIDER_BACKENDS = {
    "rules": "apps.ai_assistance.providers.rules.RuleBasedAIProvider",
    "anthropic": "apps.ai_assistance.providers.anthropic.AnthropicAIProvider",
    "openai": "apps.ai_assistance.providers.openai.OpenAIProvider",
    "gemini": "apps.ai_assistance.providers.gemini.GeminiProvider",
}


def get_provider() -> AIProvider:
    """Instantiate and validate the operator-selected replaceable provider.

    The platform-wide choice (settable from Platform Administration, no
    redeploy required) takes precedence; AI_PROVIDER_BACKEND remains a
    deploy-time fallback for an unrecognised or not-yet-configured value.
    """
    from apps.platform_admin.models import PlatformConfiguration

    config = PlatformConfiguration.load()
    backend_path = PROVIDER_BACKENDS.get(config.ai_provider_key, settings.AI_PROVIDER_BACKEND)
    provider_class = import_string(backend_path)
    provider = provider_class()
    text_attributes = ["key", "label", "model_identifier"]
    for attribute in text_attributes:
        value = getattr(provider, attribute, None)
        if not isinstance(value, str) or not value.strip():
            raise TypeError(
                f"Configured AI provider requires a non-empty '{attribute}' string."
            )
    callable_attributes = ["review_decision", "summarise_analytics", "test_connection"]
    for attribute in callable_attributes:
        if not callable(getattr(provider, attribute, None)):
            raise TypeError(
                f"Configured AI provider requires a callable '{attribute}' method."
            )
    return provider
