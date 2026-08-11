"""Real-model decision review via the OpenAI API.

Mirrors AnthropicAIProvider exactly: same schema, same sanitisation, same
advisory-only constraint. Only the wire format for tool calling differs.
"""

from __future__ import annotations

import json
from typing import Any

import openai

from apps.platform_admin.crypto import decrypt_secret
from apps.platform_admin.models import PlatformConfiguration

from . import _analytics_shared as analytics_shared
from . import _review_shared as shared
from .base import AIReviewOutput, AnalyticsNarrative, ProviderConnectionResult


class OpenAIProvider:
    """Real-LLM decision review backed by the OpenAI Chat Completions API."""

    key = "openai"
    label = "OpenAI ChatGPT"

    def __init__(self) -> None:
        config = PlatformConfiguration.load()
        if not config.ai_provider_api_key_is_set:
            raise ValueError(
                "No OpenAI API key is configured. Set one from Platform "
                "Administration before selecting this provider."
            )
        self.model_identifier = config.ai_provider_model.strip() or "gpt-4o"
        self._api_key = decrypt_secret(config.ai_provider_api_key_encrypted)

    def review_decision(self, *, snapshot: dict[str, Any]) -> AIReviewOutput:
        client = openai.OpenAI(api_key=self._api_key)
        tool = {
            "type": "function",
            "function": {
                "name": shared.REVIEW_TOOL_NAME,
                "description": shared.REVIEW_TOOL_DESCRIPTION,
                "parameters": shared.REVIEW_PARAMETERS_SCHEMA,
            },
        }
        response = client.chat.completions.create(
            model=self.model_identifier,
            messages=[
                {"role": "system", "content": shared.SYSTEM_PROMPT},
                {"role": "user", "content": shared.review_user_message(snapshot)},
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": shared.REVIEW_TOOL_NAME}},
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        call = next((item for item in tool_calls if item.function.name == shared.REVIEW_TOOL_NAME), None)
        if call is None:
            raise ValueError("The AI provider did not return a structured review.")
        try:
            payload: dict[str, Any] = json.loads(call.function.arguments)
        except (TypeError, ValueError) as error:
            raise ValueError("The AI provider returned an unparseable structured review.") from error
        return shared.build_review_output(payload=payload, snapshot=snapshot, provider_label=self.label)

    def summarise_analytics(self, *, metrics: dict[str, Any]) -> AnalyticsNarrative:
        client = openai.OpenAI(api_key=self._api_key)
        tool = {
            "type": "function",
            "function": {
                "name": analytics_shared.NARRATIVE_TOOL_NAME,
                "description": analytics_shared.NARRATIVE_TOOL_DESCRIPTION,
                "parameters": analytics_shared.NARRATIVE_PARAMETERS_SCHEMA,
            },
        }
        response = client.chat.completions.create(
            model=self.model_identifier,
            messages=[
                {"role": "system", "content": analytics_shared.SYSTEM_PROMPT},
                {"role": "user", "content": analytics_shared.narrative_user_message(metrics)},
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": analytics_shared.NARRATIVE_TOOL_NAME}},
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        call = next((item for item in tool_calls if item.function.name == analytics_shared.NARRATIVE_TOOL_NAME), None)
        if call is None:
            raise ValueError("The AI provider did not return a structured narrative.")
        try:
            payload: dict[str, Any] = json.loads(call.function.arguments)
        except (TypeError, ValueError) as error:
            raise ValueError("The AI provider returned an unparseable structured narrative.") from error
        return analytics_shared.build_narrative(payload=payload, provider_label=self.label)

    def test_connection(self) -> ProviderConnectionResult:
        try:
            client = openai.OpenAI(api_key=self._api_key)
            client.chat.completions.create(
                model=self.model_identifier,
                max_tokens=8,
                messages=[{"role": "user", "content": "Reply with the single word OK."}],
            )
        except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
            return ProviderConnectionResult(ok=False, detail=str(error))
        return ProviderConnectionResult(ok=True, detail=f"Reached the OpenAI API with model {self.model_identifier}.")
