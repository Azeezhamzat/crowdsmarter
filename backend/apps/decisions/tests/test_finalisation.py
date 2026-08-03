import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditEvent
from apps.decision_options.models import DecisionOption
from apps.decisions.finalisation import DecisionFinalisationError, finalise_decision
from apps.decisions.models import Decision, DecisionFinalisation
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.positions.models import Position
from apps.positions.services import submit_position


def add_decision_maker(*, decision, user):  # type: ignore[no-untyped-def]
    Membership.objects.create(
        organisation=decision.organisation,
        user=user,
        role=Membership.Role.CONTRIBUTOR,
    )
    return Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=user,
        role=Participant.Role.DECISION_MAKER,
        added_by=decision.owner,
    )


@pytest.mark.django_db
def test_human_finalisation_selects_option_and_records_snapshot(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    decision_maker = user_factory()
    add_decision_maker(decision=decision, user=decision_maker)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Run a pilot",
        description="Test the approach for three months.",
    )
    for actor in (decision.owner, decision_maker):
        submit_position(
            actor=actor,
            decision=decision,
            preferred_option_id=option.id,
            recommendation=Position.Recommendation.SUPPORT,
            rationale="The pilot balances learning and risk.",
            confidence=Position.Confidence.HIGH,
        )

    record = finalise_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.READY_FOR_DECISION,
        selected_option_id=option.id,
        rationale="The pilot provides sufficient learning before wider commitment.",
        conditions="Review results after three months.",
        dissent_summary="",
        positions_reviewed=True,
    )
    decision.refresh_from_db()

    assert record.selected_option == option
    assert len(record.position_snapshot) == 2
    assert decision.status == Decision.Status.DECISION_FINALISED
    assert decision.transitions.latest("sequence").to_status == Decision.Status.DECISION_FINALISED
    assert AuditEvent.objects.filter(
        action="decision.finalised",
        object_id=str(record.id),
    ).exists()


@pytest.mark.django_db
def test_finalisation_requires_every_active_authority_position(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    decision_maker = user_factory()
    add_decision_maker(decision=decision, user=decision_maker)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Pilot",
        description="Run a limited pilot.",
    )
    submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=option.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="Proceed with a pilot.",
        confidence=Position.Confidence.MEDIUM,
    )

    with pytest.raises(DecisionFinalisationError) as exc_info:
        finalise_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.READY_FOR_DECISION,
            selected_option_id=option.id,
            rationale="Proceed.",
            positions_reviewed=True,
        )

    assert any(
        decision_maker.email in message for message in exc_info.value.message_dict["positions"]
    )


@pytest.mark.django_db
def test_finalisation_requires_dissent_summary(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    decision_maker = user_factory()
    add_decision_maker(decision=decision, user=decision_maker)
    selected = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Pilot",
        description="Run a pilot.",
    )
    alternative = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Do nothing",
        description="Continue current practice.",
    )
    submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=selected.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="The pilot is proportionate.",
        confidence=Position.Confidence.HIGH,
    )
    submit_position(
        actor=decision_maker,
        decision=decision,
        preferred_option_id=alternative.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="Current practice has lower operational risk.",
        confidence=Position.Confidence.MEDIUM,
    )

    with pytest.raises(DecisionFinalisationError) as exc_info:
        finalise_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.READY_FOR_DECISION,
            selected_option_id=selected.id,
            rationale="The learning value outweighs the operational burden.",
            positions_reviewed=True,
        )

    assert "dissent_summary" in exc_info.value.message_dict


@pytest.mark.django_db
def test_ordinary_contributor_cannot_finalise(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Pilot",
        description="Run a pilot.",
    )

    with pytest.raises(PermissionDenied):
        finalise_decision(
            actor=contributor,
            decision=decision,
            expected_status=Decision.Status.READY_FOR_DECISION,
            selected_option_id=option.id,
            rationale="Attempted finalisation.",
            positions_reviewed=True,
        )


@pytest.mark.django_db
def test_finalisation_record_is_immutable(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Pilot",
        description="Run a pilot.",
    )
    submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=option.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="Proceed with a pilot.",
        confidence=Position.Confidence.HIGH,
    )
    record = finalise_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.READY_FOR_DECISION,
        selected_option_id=option.id,
        rationale="The pilot is the proportionate choice.",
        positions_reviewed=True,
    )

    record.rationale = "Changed later"
    with pytest.raises(ValidationError, match="immutable"):
        record.save()
    with pytest.raises(ValidationError, match="immutable"):
        DecisionFinalisation.objects.filter(id=record.id).delete()


@pytest.mark.django_db
def test_designated_decision_maker_may_finalise(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    decision_maker = user_factory()
    add_decision_maker(decision=decision, user=decision_maker)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Pilot",
        description="Run a controlled pilot.",
    )
    for actor in (decision.owner, decision_maker):
        submit_position(
            actor=actor,
            decision=decision,
            preferred_option_id=option.id,
            recommendation=Position.Recommendation.SUPPORT,
            rationale="A pilot is proportionate.",
            confidence=Position.Confidence.HIGH,
        )

    record = finalise_decision(
        actor=decision_maker,
        decision=decision,
        expected_status=Decision.Status.READY_FOR_DECISION,
        selected_option_id=option.id,
        rationale="The required authorities support a controlled pilot.",
        positions_reviewed=True,
    )

    assert record.decided_by == decision_maker


@pytest.mark.django_db
def test_finalisation_rejects_stale_expected_status(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Pilot",
        description="Run a controlled pilot.",
    )

    with pytest.raises(DecisionFinalisationError) as exc_info:
        finalise_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.UNDER_REVIEW,
            selected_option_id=option.id,
            rationale="Attempted from a stale page.",
            positions_reviewed=True,
        )

    assert "expected_status" in exc_info.value.message_dict
