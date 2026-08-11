"""Real-model decision review via the Google Gemini API.

Mirrors AnthropicAIProvider and OpenAIProvider exactly: same schema, same
sanitisation, same advisory-only constraint. Gemini's structured-output mode
is driven by a JSON-mime response plus an explicit shape description in the
prompt (rather than a converted schema object), since the cleaning layer in
_review_shared already tolerates a loosely-shaped payload safely.
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types as genai_types

from apps.platform_admin.crypto import decrypt_secret
from apps.platform_admin.models import PlatformConfiguration

from . import _analytics_shared as analytics_shared
from . import _review_shared as shared
from .base import AIReviewOutput, AnalyticsNarrative, ProviderConnectionResult

_SHAPE_INSTRUCTIONS = f"""

Respond with a single JSON object matching exactly this shape (omit nothing, use \
empty arrays/strings where you have no finding):

{json.dumps(shared.REVIEW_PARAMETERS_SCHEMA, indent=2)}
"""

_NARRATIVE_SHAPE_INSTRUCTIONS = f"""

Respond with a single JSON object matching exactly this shape (omit nothing, use \
an empty array if there are no observations):

{json.dumps(analytics_shared.NARRATIVE_PARAMETERS_SCHEMA, indent=2)}
"""


class GeminiProvider:
    """Real-LLM decision review backed by the Google Gemini API."""

    key = "gemini"
    label = "Google Gemini"

    def __init__(self) -> None:
        config = PlatformConfiguration.load()
        if not config.ai_provider_api_key_is_set:
            raise ValueError(
                "No Gemini API key is configured. Set one from Platform "
                "Administration before selecting this provider."
            )
        self.model_identifier = config.ai_provider_model.strip() or "gemini-2.0-flash"
        self._api_key = decrypt_secret(config.ai_provider_api_key_encrypted)

    def review_decision(self, *, snapshot: dict[str, Any]) -> AIReviewOutput:
        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=self.model_identifier,
            contents=shared.SYSTEM_PROMPT + _SHAPE_INSTRUCTIONS + "\n\n" + shared.review_user_message(snapshot),
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("The AI provider did not return a structured review.")
        try:
            payload: dict[str, Any] = json.loads(text)
        except (TypeError, ValueError) as error:
            raise ValueError("The AI provider returned an unparseable structured review.") from error
        if not isinstance(payload, dict):
            raise ValueError("The AI provider did not return a structured review.")
        return shared.build_review_output(payload=payload, snapshot=snapshot, provider_label=self.label)

    def summarise_analytics(self, *, metrics: dict[str, Any]) -> AnalyticsNarrative:
        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=self.model_identifier,
            contents=(
                analytics_shared.SYSTEM_PROMPT
                + _NARRATIVE_SHAPE_INSTRUCTIONS
                + "\n\n"
                + analytics_shared.narrative_user_message(metrics)
            ),
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("The AI provider did not return a structured narrative.")
        try:
            payload: dict[str, Any] = json.loads(text)
        except (TypeError, ValueError) as error:
            raise ValueError("The AI provider returned an unparseable structured narrative.") from error
        if not isinstance(payload, dict):
            raise ValueError("The AI provider did not return a structured narrative.")
        return analytics_shared.build_narrative(payload=payload, provider_label=self.label)

    def test_connection(self) -> ProviderConnectionResult:
        try:
            client = genai.Client(api_key=self._api_key)
            client.models.generate_content(
                model=self.model_identifier,
                contents="Reply with the single word OK.",
            )
        except Exception as error:  # noqa: BLE001 - surface any failure as a diagnosable result
            return ProviderConnectionResult(ok=False, detail=str(error))
        return ProviderConnectionResult(ok=True, detail=f"Reached the Gemini API with model {self.model_identifier}.")
