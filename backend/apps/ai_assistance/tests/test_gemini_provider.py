import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from apps.ai_assistance.providers.gemini import GeminiProvider
from apps.ai_assistance.providers.registry import get_provider
from apps.platform_admin.crypto import encrypt_secret
from apps.platform_admin.models import PlatformConfiguration

SNAPSHOT = {
    "decision": {
        "title": "Pilot decision",
        "decision_question": "Should we run the pilot?",
        "purpose": "Learn before scaling.",
        "context": "Current evidence is limited.",
    },
    "options": [{"id": "option-1", "title": "Run pilot"}],
    "evidence": [{"id": "evidence-1", "title": "Survey", "summary": "x", "option_id": None, "stance": "supports"}],
    "assumptions": [],
    "risks": [],
    "participants": [{"role": "decision_owner"}],
    "historical_decisions": [{"id": "past-1", "title": "Earlier pilot", "status": "archived"}],
    "generated_at": "2026-01-01T00:00:00+00:00",
}


def _fake_response(payload):
    return SimpleNamespace(text=json.dumps(payload))


@pytest.mark.django_db
def test_raises_when_no_key_is_configured():
    with pytest.raises(ValueError, match="No Gemini API key is configured"):
        GeminiProvider()


@pytest.mark.django_db
def test_parses_a_well_formed_json_response_into_ai_review_output():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("gm-test-key")
    config.ai_provider_model = "gemini-2.0-flash"
    config.save(update_fields=["ai_provider_api_key_encrypted", "ai_provider_model"])

    payload = {
        "summary": "The pilot has thin evidence.",
        "missing_evidence": [
            {"severity": "medium", "title": "No challenging evidence", "detail": "Only supportive evidence is recorded."}
        ],
        "unsupported_assumptions": [],
        "contradictory_evidence": [],
        "duplicate_evidence": [],
        "missing_stakeholders": [],
        "risk_highlights": [],
        "review_triggers": [],
        "similar_decisions": [
            {"decision_id": "past-1", "similarity": 0.42, "reason": "Same domain and framing."}
        ],
        "limitations": [],
    }

    with patch("apps.ai_assistance.providers.gemini.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.models.generate_content.return_value = _fake_response(payload)
        provider = GeminiProvider()
        output = provider.review_decision(snapshot=SNAPSHOT)

    assert provider.model_identifier == "gemini-2.0-flash"
    assert output.summary == payload["summary"]
    assert output.missing_evidence[0].title == "No challenging evidence"
    assert output.similar_decisions[0].decision_id == "past-1"
    assert any("large language model" in note.lower() for note in output.limitations)


@pytest.mark.django_db
def test_raises_when_the_model_returns_empty_text():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("gm-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    with patch("apps.ai_assistance.providers.gemini.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.models.generate_content.return_value = SimpleNamespace(text="")
        with pytest.raises(ValueError, match="did not return a structured review"):
            GeminiProvider().review_decision(snapshot=SNAPSHOT)


@pytest.mark.django_db
def test_raises_when_the_model_returns_unparseable_text():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("gm-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    with patch("apps.ai_assistance.providers.gemini.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.models.generate_content.return_value = SimpleNamespace(text="not json")
        with pytest.raises(ValueError, match="unparseable structured review"):
            GeminiProvider().review_decision(snapshot=SNAPSHOT)


@pytest.mark.django_db
def test_registry_returns_gemini_provider_once_selected():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("gm-test-key")
    config.ai_provider_key = PlatformConfiguration.AIProviderKey.GEMINI
    config.save(update_fields=["ai_provider_api_key_encrypted", "ai_provider_key"])

    assert isinstance(get_provider(), GeminiProvider)


@pytest.mark.django_db
def test_summarise_analytics_parses_a_well_formed_narrative():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("gm-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    metrics = {
        "totals": {"decisions": 1, "open_decisions": 1, "finalised_decisions": 0, "archived_decisions": 0, "active_lessons": 0},
        "flow": {"overdue_target_decisions": 0, "contribution_coverage_percent": None, "median_days_to_finalise": None, "created_last_90_days": 1, "finalised_last_90_days": 0},
        "learning": {"reviews_due_or_overdue": 0, "outcome_success_percent": None, "outcome_reviews_completed": 0, "active_lessons": 0},
    }
    payload = {
        "headline": "One decision is open; not enough history for trends yet.",
        "observations": [],
    }

    with patch("apps.ai_assistance.providers.gemini.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.models.generate_content.return_value = _fake_response(payload)
        narrative = GeminiProvider().summarise_analytics(metrics=metrics)

    assert narrative.headline == payload["headline"]
    assert narrative.observations == []
    assert narrative.generated_by == "Google Gemini"
