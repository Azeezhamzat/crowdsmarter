import pytest
from django.core.exceptions import ValidationError

from apps.contributions.models import ContributionRequest, ContributionSubmission
from apps.contributions.services import (
    create_request,
    review_submission,
    save_draft,
    submit_request,
)
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_contribution_request_preserves_draft_submission_and_review_history(
    decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    assignee = user_factory(email="contributor@example.com")
    reviewer = user_factory(email="reviewer@example.com")
    for user in [assignee, reviewer]:
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=assignee,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=reviewer,
        role=Participant.Role.REVIEWER,
        added_by=decision.owner,
    )

    request = create_request(
        actor=decision.owner,
        decision=decision,
        assignee_id=assignee.id,
        reviewer_id=reviewer.id,
        kind="evidence",
        title="Validate implementation evidence",
        instructions="Review the source and record the limitations.",
    )
    draft = save_draft(
        actor=assignee,
        request=request,
        body="The source supports the implementation estimate with limitations.",
        references="Internal study 24-B",
    )
    assert draft.status == ContributionSubmission.Status.DRAFT

    submitted = submit_request(actor=assignee, request=request)
    request.refresh_from_db()
    assert submitted.status == ContributionSubmission.Status.SUBMITTED
    assert request.status == ContributionRequest.Status.SUBMITTED

    review_submission(
        actor=reviewer,
        request=request,
        outcome="accepted",
        note="Accepted with the limitation retained in the evidence record.",
    )
    request.refresh_from_db()
    assert request.status == ContributionRequest.Status.ACCEPTED
    assert request.reviews.count() == 1

    submitted.body = "Silent rewrite"
    with pytest.raises(ValidationError, match="immutable"):
        submitted.save()


@pytest.mark.django_db
def test_assignment_requires_active_non_observer_participant(
    decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    outsider = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=outsider,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    with pytest.raises(ValidationError, match="non-observer decision participant"):
        create_request(
            actor=decision.owner,
            decision=decision,
            assignee_id=outsider.id,
            reviewer_id=None,
            kind="question",
            title="Answer the framing question",
            instructions="Provide a bounded response.",
        )


@pytest.mark.django_db
def test_facilitation_sessions_follow_forward_only_transitions(
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import (
        ContributionServiceError,
        create_session,
        update_session_status,
    )

    decision = decision_factory(status="open_for_contribution")
    session = create_session(
        actor=decision.owner,
        decision=decision,
        title="Evidence interpretation workshop",
        objective="Agree the remaining evidence questions without pre-deciding the option.",
    )
    session = update_session_status(actor=decision.owner, session=session, status="open")
    with pytest.raises(ContributionServiceError, match="cannot move"):
        update_session_status(actor=decision.owner, session=session, status="planned")
    session = update_session_status(actor=decision.owner, session=session, status="closed")
    assert session.status == "closed"


@pytest.mark.django_db
def test_request_can_be_reassigned_before_work_but_not_after_a_draft_exists(
    decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import ContributionServiceError, update_request

    decision = decision_factory(status="open_for_contribution")
    first = user_factory(email="first-assignee@example.com")
    second = user_factory(email="second-assignee@example.com")
    for user in [first, second]:
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
            status=Membership.Status.ACTIVE,
        )
        Participant.objects.create(
            organisation=decision.organisation,
            decision=decision,
            user=user,
            role=Participant.Role.CONTRIBUTOR,
            added_by=decision.owner,
        )
    request = create_request(
        actor=decision.owner,
        decision=decision,
        assignee_id=first.id,
        reviewer_id=None,
        kind="question",
        title="Clarify the implementation dependency",
        instructions="Record the dependency and its evidence boundary.",
    )
    request = update_request(
        actor=decision.owner,
        request=request,
        changes={"assignee_id": second.id, "priority": "high"},
    )
    assert request.assignee == second
    assert request.priority == "high"

    save_draft(
        actor=second,
        request=request,
        body="The dependency is bounded by supplier approval.",
    )
    with pytest.raises(ContributionServiceError, match="cannot be reassigned"):
        update_request(
            actor=decision.owner,
            request=request,
            changes={"assignee_id": first.id},
        )
