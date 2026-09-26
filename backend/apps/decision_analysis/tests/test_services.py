import pytest
from django.core.exceptions import ValidationError

from apps.decision_analysis.models import DecisionQualityReview, ExecutiveDecisionSummary
from apps.decision_analysis.services import (
    create_executive_summary,
    create_quality_review,
    update_executive_summary,
    update_quality_review,
)


@pytest.mark.django_db
def test_publishing_review_supersedes_previous_version(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    first = create_quality_review(
        actor=decision.owner, decision=decision, judgement="not_ready", answers={}
    )
    first = update_quality_review(
        actor=decision.owner, review=first, fields={"status": "published"}
    )
    second = create_quality_review(
        actor=decision.owner, decision=decision, judgement="ready", answers={}
    )
    second = update_quality_review(
        actor=decision.owner, review=second, fields={"status": "published"}
    )
    first.refresh_from_db()
    assert first.status == DecisionQualityReview.Status.SUPERSEDED
    assert second.status == DecisionQualityReview.Status.PUBLISHED
    assert second.version == 2


@pytest.mark.django_db
def test_approved_summary_is_immutable(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    summary = create_executive_summary(
        actor=decision.owner,
        decision=decision,
        proposed_judgement="Proceed conditionally.",
    )
    summary = update_executive_summary(
        actor=decision.owner,
        summary=summary,
        fields={"status": "approved"},
    )
    assert summary.status == ExecutiveDecisionSummary.Status.APPROVED
    with pytest.raises(ValidationError):
        update_executive_summary(
            actor=decision.owner,
            summary=summary,
            fields={"proposed_judgement": "Silently changed."},
        )


@pytest.mark.django_db
def test_issue_owner_can_resolve_but_cannot_transfer_ownership(decision_factory, user_factory):  # type: ignore[no-untyped-def]
    from django.core.exceptions import PermissionDenied

    from apps.decision_analysis.services import create_issue, update_issue
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    decision = decision_factory()
    contributor = user_factory()
    other = user_factory()
    for user in (contributor, other):
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    issue = create_issue(
        actor=contributor,
        decision=decision,
        owner_id=contributor.id,
        issue_type="unsupported_assumption",
        title="Assumption needs verification",
        description="The assumption lacks current evidence.",
    )

    with pytest.raises(PermissionDenied):
        update_issue(
            actor=contributor,
            issue=issue,
            fields={"owner_id": other.id},
        )

    resolved = update_issue(
        actor=contributor,
        issue=issue,
        fields={"status": "resolved", "resolution": "Verified against the latest source."},
    )
    assert resolved.status == "resolved"
    assert resolved.resolved_by == contributor
