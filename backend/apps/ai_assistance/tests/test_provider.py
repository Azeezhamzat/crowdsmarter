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


def test_rules_provider_summarises_analytics_with_no_decisions():
    metrics = {
        "totals": {
            "decisions": 0,
            "open_decisions": 0,
            "finalised_decisions": 0,
            "archived_decisions": 0,
            "active_lessons": 0,
        },
        "flow": {
            "overdue_target_decisions": 0,
            "contribution_coverage_percent": None,
            "median_days_to_finalise": None,
            "created_last_90_days": 0,
            "finalised_last_90_days": 0,
        },
        "learning": {
            "reviews_due_or_overdue": 0,
            "outcome_success_percent": None,
            "outcome_reviews_completed": 0,
            "active_lessons": 0,
        },
    }
    narrative = RuleBasedAIProvider().summarise_analytics(metrics=metrics)
    assert "no decisions" in narrative.headline.lower()
    assert narrative.observations


def test_rules_provider_flags_overdue_decisions_and_low_coverage():
    metrics = {
        "totals": {
            "decisions": 4,
            "open_decisions": 3,
            "finalised_decisions": 1,
            "archived_decisions": 0,
            "active_lessons": 0,
        },
        "flow": {
            "overdue_target_decisions": 2,
            "contribution_coverage_percent": 33.3,
            "median_days_to_finalise": 90.0,
            "created_last_90_days": 4,
            "finalised_last_90_days": 1,
        },
        "learning": {
            "reviews_due_or_overdue": 1,
            "outcome_success_percent": 40.0,
            "outcome_reviews_completed": 5,
            "active_lessons": 0,
        },
    }
    narrative = RuleBasedAIProvider().summarise_analytics(metrics=metrics)
    titles = [item.title for item in narrative.observations]
    assert any("past their target date" in title for title in titles)
    assert any("coverage is low" in title for title in titles)
    assert any("due or overdue" in title for title in titles)
    assert any("Median time to finalise" in title for title in titles)
    assert narrative.generated_by == "Transparent rules review"
    high_severities = [
        item.severity for item in narrative.observations if "target date" in item.title
    ]
    assert high_severities == ["high"]
