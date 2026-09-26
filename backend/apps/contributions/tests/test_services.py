import pytest
from django.core.exceptions import ValidationError

from apps.contributions.models import (
    ContributionRequest,
    ContributionSubmission,
    FacilitationAuthorityResponse,
    FacilitationRecord,
    SessionParticipant,
)
from apps.contributions.services import (
    ContributionServiceError,
    create_facilitation_record,
    create_request,
    create_session,
    review_submission,
    save_draft,
    save_facilitation_authority_response,
    submit_request,
    update_session_status,
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
def test_assignment_requires_active_non_observer_participant(decision_factory, user_factory):  # type: ignore[no-untyped-def]
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
def test_facilitator_captures_provenance_without_leaking_anonymous_identity(
    decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    participant_user = user_factory(email="workshop-participant@example.com")
    Membership.objects.create(
        organisation=decision.organisation,
        user=participant_user,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=participant_user,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    session = create_session(
        actor=decision.owner,
        decision=decision,
        title="Hybrid evidence session",
        objective="Capture evidence from in-person and telephone participants.",
        influence_boundary="Evidence weighting and implementation conditions.",
        fixed_constraints="The statutory deadline.",
        participation_channels=["in_person", "phone"],
        participants=[{"user_id": participant_user.id, "role": "participant"}],
    )
    session = update_session_status(actor=decision.owner, session=session, status="open")
    source = session.participants.get(user=participant_user)

    record = create_facilitation_record(
        actor=decision.owner,
        session=session,
        kind="evidence_gap",
        body="Telephone participants could not verify the baseline estimate.",
        channel="phone",
        origin="participant_input",
        attribution="confidential",
        source_participant_id=source.id,
        permission_to_quote=False,
        follow_up_owner="Evidence lead",
    )

    assert record.source_participant == source
    assert record.channel == FacilitationRecord.Channel.PHONE
    assert record.follow_up_owner == "Evidence lead"
    with pytest.raises(ValidationError, match="Anonymous records cannot retain"):
        create_facilitation_record(
            actor=decision.owner,
            session=session,
            kind="agreement",
            body="A purported anonymous statement.",
            channel="in_person",
            origin="participant_input",
            attribution="anonymous",
            source_participant_id=source.id,
        )


@pytest.mark.django_db
def test_authority_response_requires_closed_session_and_becomes_immutable(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status="open_for_contribution")
    session = create_session(
        actor=decision.owner,
        decision=decision,
        title="Implementation workshop",
        objective="Test implementation conditions.",
    )
    session = update_session_status(actor=decision.owner, session=session, status="open")
    draft = save_facilitation_authority_response(
        actor=decision.owner,
        session=session,
        what_we_heard="Participants need a clearer delivery timetable.",
        what_changed="The timetable will include decision gates.",
        what_did_not_change="",
        rationale="",
        next_steps="Publish the revised timetable next week.",
    )
    assert draft.status == FacilitationAuthorityResponse.Status.DRAFT
    with pytest.raises(ContributionServiceError, match="Close the session"):
        save_facilitation_authority_response(
            actor=decision.owner,
            session=session,
            what_we_heard=draft.what_we_heard,
            what_changed=draft.what_changed,
            what_did_not_change="",
            rationale="",
            next_steps=draft.next_steps,
            publish=True,
        )

    session = update_session_status(actor=decision.owner, session=session, status="closed")
    published = save_facilitation_authority_response(
        actor=decision.owner,
        session=session,
        what_we_heard=draft.what_we_heard,
        what_changed=draft.what_changed,
        what_did_not_change="",
        rationale="",
        next_steps=draft.next_steps,
        publish=True,
    )
    assert published.status == FacilitationAuthorityResponse.Status.PUBLISHED
    assert published.published_by == decision.owner
    with pytest.raises(ContributionServiceError, match="immutable"):
        save_facilitation_authority_response(
            actor=decision.owner,
            session=session,
            what_we_heard="A rewritten account.",
            what_changed=draft.what_changed,
            what_did_not_change="",
            rationale="",
            next_steps=draft.next_steps,
        )


@pytest.mark.django_db
def test_facilitation_session_preserves_participant_and_observer_roles(
    decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import create_session

    decision = decision_factory(status="open_for_contribution")
    contributor = user_factory(email="participant@example.com")
    observer = user_factory(email="observer@example.com")
    for user in [contributor, observer]:
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
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
        added_by=decision.owner,
    )

    session = create_session(
        actor=decision.owner,
        decision=decision,
        title="Decision framing workshop",
        objective="Clarify the question, authority, and participation boundary.",
        participants=[
            {"user_id": contributor.id, "role": SessionParticipant.Role.PARTICIPANT},
            {"user_id": observer.id, "role": SessionParticipant.Role.OBSERVER},
        ],
    )

    assert list(
        session.participants.order_by("user__email").values_list("user__email", "role")
    ) == [
        ("observer@example.com", SessionParticipant.Role.OBSERVER),
        ("participant@example.com", SessionParticipant.Role.PARTICIPANT),
    ]


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
