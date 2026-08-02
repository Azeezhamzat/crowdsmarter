from apps.ai_assistance.providers.rules import RuleBasedAIProvider


def test_rules_provider_surfaces_explicit_gaps_without_mutation():
    snapshot = {
        "decision": {
            "title": "Pilot decision",
            "decision_question": "Should we run the pilot?",
            "purpose": "Learn before scaling.",
            "context": "Current evidence is limited.",
        },
        "options": [{"id": "option-1", "title": "Run pilot"}],
        "evidence": [],
        "assumptions": [],
        "risks": [],
        "participants": [{"role": "decision_owner"}],
        "historical_decisions": [],
    }
    output = RuleBasedAIProvider().review_decision(snapshot=snapshot)
    assert output.missing_evidence
    assert output.unsupported_assumptions
    assert output.missing_stakeholders
    assert output.risk_highlights
    assert "human" in " ".join(output.limitations).lower()
