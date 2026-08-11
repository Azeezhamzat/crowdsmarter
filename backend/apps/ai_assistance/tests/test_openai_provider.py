import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from apps.ai_assistance.providers.openai import OpenAIProvider
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
    tool_call = SimpleNamespace(
        function=SimpleNamespace(name="submit_decision_review", arguments=json.dumps(payload))
    )
    message = SimpleNamespace(tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@pytest.mark.django_db
def test_raises_when_no_key_is_configured():
    with pytest.raises(ValueError, match="No OpenAI API key is configured"):
        OpenAIProvider()


@pytest.mark.django_db
def test_parses_a_well_formed_tool_response_into_ai_review_output():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-openai-test-key")
    config.ai_provider_model = "gpt-4o"
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

    with patch("apps.ai_assistance.providers.openai.openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = _fake_response(payload)
        provider = OpenAIProvider()
        output = provider.review_decision(snapshot=SNAPSHOT)

    assert provider.model_identifier == "gpt-4o"
    assert output.summary == payload["summary"]
    assert output.missing_evidence[0].title == "No challenging evidence"
    assert output.similar_decisions[0].decision_id == "past-1"
    assert any("large language model" in note.lower() for note in output.limitations)


@pytest.mark.django_db
def test_strips_hallucinated_related_ids():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-openai-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    payload = {
        "summary": "Summary text.",
        "missing_evidence": [
            {
                "severity": "high",
                "title": "References a made-up evidence id",
                "detail": "Detail text.",
                "related_type": "evidence",
                "related_id": "evidence-does-not-exist",
            }
        ],
        "unsupported_assumptions": [],
        "contradictory_evidence": [],
        "duplicate_evidence": [],
        "missing_stakeholders": [],
        "risk_highlights": [],
        "review_triggers": [],
        "similar_decisions": [],
        "limitations": [],
    }

    with patch("apps.ai_assistance.providers.openai.openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = _fake_response(payload)
        output = OpenAIProvider().review_decision(snapshot=SNAPSHOT)

    assert output.missing_evidence[0].related_id == ""


@pytest.mark.django_db
def test_raises_when_the_model_returns_no_tool_call():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-openai-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    with patch("apps.ai_assistance.providers.openai.openai.OpenAI") as mock_client_cls:
        message = SimpleNamespace(tool_calls=None)
        mock_client_cls.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=message)]
        )
        with pytest.raises(ValueError, match="did not return a structured review"):
            OpenAIProvider().review_decision(snapshot=SNAPSHOT)


@pytest.mark.django_db
def test_registry_returns_openai_provider_once_selected():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-openai-test-key")
    config.ai_provider_key = PlatformConfiguration.AIProviderKey.OPENAI
    config.save(update_fields=["ai_provider_api_key_encrypted", "ai_provider_key"])

    assert isinstance(get_provider(), OpenAIProvider)


@pytest.mark.django_db
def test_summarise_analytics_parses_a_well_formed_narrative():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-openai-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    metrics = {
        "totals": {"decisions": 3, "open_decisions": 2, "finalised_decisions": 1, "archived_decisions": 0, "active_lessons": 1},
        "flow": {"overdue_target_decisions": 0, "contribution_coverage_percent": 100.0, "median_days_to_finalise": 5.0, "created_last_90_days": 3, "finalised_last_90_days": 1},
        "learning": {"reviews_due_or_overdue": 0, "outcome_success_percent": 100.0, "outcome_reviews_completed": 1, "active_lessons": 1},
    }
    payload = {
        "headline": "All open decisions have strong coverage.",
        "observations": [
            {"severity": "low", "title": "Full contribution coverage", "detail": "Every open decision has two or more participants."},
        ],
    }

    tool_call = SimpleNamespace(
        function=SimpleNamespace(name="submit_analytics_narrative", arguments=json.dumps(payload))
    )
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tool_call]))])

    with patch("apps.ai_assistance.providers.openai.openai.OpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create.return_value = response
        narrative = OpenAIProvider().summarise_analytics(metrics=metrics)

    assert narrative.headline == payload["headline"]
    assert narrative.observations[0].severity == "low"
    assert narrative.generated_by == "OpenAI ChatGPT"
