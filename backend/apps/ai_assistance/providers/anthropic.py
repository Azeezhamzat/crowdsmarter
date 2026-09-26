"""Real-model decision review via the Anthropic API.

Produces the exact same AIReviewOutput shape as the rules provider, so the
rest of the app (storage, display, human review/dismissal, quality metrics)
is completely provider-agnostic. The model is explicitly instructed to stay
advisory only, mirroring the constraint the rules provider already
satisfies structurally: it can surface findings, it cannot alter records,
choose an option, or exercise decision authority.
"""

from __future__ import annotations

from typing import Any

import anthropic

from apps.platform_admin.crypto import decrypt_secret
from apps.platform_admin.models import PlatformConfiguration

from . import _analytics_shared as analytics_shared
from . import _review_shared as shared
from .base import AIReviewOutput, AnalyticsNarrative, ProviderConnectionResult


class AnthropicAIProvider:
    """Real-LLM decision review backed by the Anthropic Messages API."""

    key = "anthropic"
    label = "Anthropic Claude"

    def __init__(self) -> None:
        config = PlatformConfiguration.load()
        if not config.ai_provider_api_key_is_set:
            raise ValueError(
                "No Anthropic API key is configured. Set one from Platform "
                "Administration before selecting this provider."
            )
        self.model_identifier = config.ai_provider_model.strip() or "claude-sonnet-5"
        self._api_key = decrypt_secret(config.ai_provider_api_key_encrypted)

    def review_decision(self, *, snapshot: dict[str, Any]) -> AIReviewOutput:
        client = anthropic.Anthropic(api_key=self._api_key)
        tool = {
            "name": shared.REVIEW_TOOL_NAME,
            "description": shared.REVIEW_TOOL_DESCRIPTION,
            "input_schema": shared.REVIEW_PARAMETERS_SCHEMA,
        }
        message = client.messages.create(  # type: ignore[call-overload]  # Dynamic JSON schema conforms to the provider API.
            model=self.model_identifier,
            max_tokens=4096,
            system=shared.SYSTEM_PROMPT,
            tools=[tool],
            tool_choice={"type": "tool", "name": shared.REVIEW_TOOL_NAME},
            messages=[{"role": "user", "content": shared.review_user_message(snapshot)}],
        )
        tool_use = next(
            (block for block in message.content if block.type == "tool_use"),
            None,
        )
        if tool_use is None:
            raise ValueError("The AI provider did not return a structured review.")
        payload: dict[str, Any] = tool_use.input
        return shared.build_review_output(
            payload=payload, snapshot=snapshot, provider_label=self.label
        )

    def summarise_analytics(self, *, metrics: dict[str, Any]) -> AnalyticsNarrative:
        client = anthropic.Anthropic(api_key=self._api_key)
        tool = {
            "name": analytics_shared.NARRATIVE_TOOL_NAME,
            "description": analytics_shared.NARRATIVE_TOOL_DESCRIPTION,
            "input_schema": analytics_shared.NARRATIVE_PARAMETERS_SCHEMA,
        }
        message = client.messages.create(  # type: ignore[call-overload]  # Dynamic JSON schema conforms to the provider API.
            model=self.model_identifier,
            max_tokens=2048,
            system=analytics_shared.SYSTEM_PROMPT,
            tools=[tool],
            tool_choice={"type": "tool", "name": analytics_shared.NARRATIVE_TOOL_NAME},
            messages=[
                {"role": "user", "content": analytics_shared.narrative_user_message(metrics)}
            ],
        )
        tool_use = next(
            (block for block in message.content if block.type == "tool_use"),
            None,
        )
        if tool_use is None:
            raise ValueError("The AI provider did not return a structured narrative.")
        payload: dict[str, Any] = tool_use.input
        return analytics_shared.build_narrative(payload=payload, provider_label=self.label)

    def test_connection(self) -> ProviderConnectionResult:
        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            client.messages.create(
                model=self.model_identifier,
                max_tokens=8,
                messages=[{"role": "user", "content": "Reply with the single word OK."}],
            )
        except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
            return ProviderConnectionResult(ok=False, detail=str(error))
        return ProviderConnectionResult(
            ok=True, detail=f"Reached the Anthropic API with model {self.model_identifier}."
        )
