import pytest
from django.core.exceptions import ValidationError

from apps.decision_analysis.models import DecisionIssue, ExecutiveDecisionSummary


@pytest.mark.django_db
def test_issue_rejects_cross_decision_option(decision_factory):  # type: ignore[no-untyped-def]
    first = decision_factory()
    second = decision_factory(workspace=first.workspace, owner=first.owner)
    from apps.decision_options.models import DecisionOption

    option = DecisionOption.objects.create(
        organisation=first.organisation,
        decision=first,
        title="First option",
        description="Belongs to another decision.",
        proposed_by=first.owner,
        created_by=first.owner,
    )
    issue = DecisionIssue(
        organisation=second.organisation,
        decision=second,
        option=option,
        issue_type=DecisionIssue.IssueType.MISSING_EVIDENCE,
        title="Cross-decision link",
        description="This must be rejected.",
        owner=second.owner,
        created_by=second.owner,
    )
    with pytest.raises(ValidationError):
        issue.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_approved_summary_requires_human_attribution(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    summary = ExecutiveDecisionSummary(
        organisation=decision.organisation,
        decision=decision,
        version=1,
        status=ExecutiveDecisionSummary.Status.APPROVED,
        proposed_judgement="Proceed with option A.",
        created_by=decision.owner,
    )
    with pytest.raises(ValidationError):
        summary.full_clean(validate_unique=False, validate_constraints=False)
