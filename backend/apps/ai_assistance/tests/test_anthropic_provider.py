from types import SimpleNamespace
from unittest.mock import patch

import pytest

from apps.ai_assistance.providers.anthropic import AnthropicAIProvider
from apps.ai_assistance.providers.registry import get_provider
from apps.ai_assistance.providers.rules import RuleBasedAIProvider
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
    "evidence": [
        {
            "id": "evidence-1",
            "title": "Survey",
            "summary": "x",
            "option_id": None,
            "stance": "supports",
        }
    ],
    "assumptions": [],
    "risks": [],
    "participants": [{"role": "decision_owner"}],
    "historical_decisions": [{"id": "past-1", "title": "Earlier pilot", "status": "archived"}],
    "generated_at": "2026-01-01T00:00:00+00:00",
}


def _fake_message(payload):
    return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=payload)])


@pytest.mark.django_db
def test_raises_when_no_key_is_configured():
    with pytest.raises(ValueError, match="No Anthropic API key is configured"):
        AnthropicAIProvider()


@pytest.mark.django_db
def test_parses_a_well_formed_tool_response_into_ai_review_output():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-ant-test-key")
    config.ai_provider_model = "claude-sonnet-5"
    config.save(update_fields=["ai_provider_api_key_encrypted", "ai_provider_model"])

    payload = {
        "summary": "The pilot has thin evidence and one open risk.",
        "missing_evidence": [
            {
                "severity": "medium",
                "title": "No challenging evidence",
                "detail": "Only supportive evidence is recorded.",
            }
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
        "limitations": ["This review only considered what was explicitly recorded."],
    }

    with patch("apps.ai_assistance.providers.anthropic.anthropic.Anthropic") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = _fake_message(payload)
        provider = AnthropicAIProvider()
        output = provider.review_decision(snapshot=SNAPSHOT)

    assert provider.model_identifier == "claude-sonnet-5"
    assert output.summary == payload["summary"]
    assert output.missing_evidence[0].title == "No challenging evidence"
    assert len(output.similar_decisions) == 1
    assert output.similar_decisions[0].decision_id == "past-1"
    assert output.similar_decisions[0].title == "Earlier pilot"
    assert output.similar_decisions[0].url == "/decisions/past-1"
    assert any("large language model" in note.lower() for note in output.limitations)


@pytest.mark.django_db
def test_strips_hallucinated_related_ids_and_unknown_similar_decisions():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-ant-test-key")
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
        "similar_decisions": [
            {
                "decision_id": "decision-that-was-never-in-the-snapshot",
                "similarity": 0.9,
                "reason": "made up",
            }
        ],
        "limitations": [],
    }

    with patch("apps.ai_assistance.providers.anthropic.anthropic.Anthropic") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = _fake_message(payload)
        output = AnthropicAIProvider().review_decision(snapshot=SNAPSHOT)

    assert output.missing_evidence[0].related_id == ""
    assert output.missing_evidence[0].related_type == ""
    assert output.similar_decisions == []


@pytest.mark.django_db
def test_raises_when_the_model_returns_no_tool_use_block():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-ant-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    with patch("apps.ai_assistance.providers.anthropic.anthropic.Anthropic") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="I decided not to use the tool.")]
        )
        with pytest.raises(ValueError, match="did not return a structured review"):
            AnthropicAIProvider().review_decision(snapshot=SNAPSHOT)


@pytest.mark.django_db
def test_registry_returns_rules_provider_by_default():
    assert isinstance(get_provider(), RuleBasedAIProvider)


@pytest.mark.django_db
def test_registry_returns_anthropic_provider_once_selected():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-ant-test-key")
    config.ai_provider_key = PlatformConfiguration.AIProviderKey.ANTHROPIC
    config.save(update_fields=["ai_provider_api_key_encrypted", "ai_provider_key"])

    assert isinstance(get_provider(), AnthropicAIProvider)


@pytest.mark.django_db
def test_summarise_analytics_parses_a_well_formed_narrative():
    config = PlatformConfiguration.load()
    config.ai_provider_api_key_encrypted = encrypt_secret("sk-ant-test-key")
    config.save(update_fields=["ai_provider_api_key_encrypted"])

    metrics = {
        "totals": {
            "decisions": 3,
            "open_decisions": 2,
            "finalised_decisions": 1,
            "archived_decisions": 0,
            "active_lessons": 1,
        },
        "flow": {
            "overdue_target_decisions": 1,
            "contribution_coverage_percent": 50.0,
            "median_days_to_finalise": 12.0,
            "created_last_90_days": 3,
            "finalised_last_90_days": 1,
        },
        "learning": {
            "reviews_due_or_overdue": 0,
            "outcome_success_percent": 100.0,
            "outcome_reviews_completed": 1,
            "active_lessons": 1,
        },
    }
    payload = {
        "headline": "3 decisions tracked; one is overdue.",
        "observations": [
            {"severity": "high", "title": "1 decision overdue", "detail": "Past its target date."},
        ],
    }

    with patch("apps.ai_assistance.providers.anthropic.anthropic.Anthropic") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = _fake_message(payload)
        narrative = AnthropicAIProvider().summarise_analytics(metrics=metrics)

    assert narrative.headline == payload["headline"]
    assert narrative.observations[0].title == "1 decision overdue"
    assert narrative.generated_by == "Anthropic Claude"
