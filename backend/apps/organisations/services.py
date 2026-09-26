"""Transactional organisation and membership workflows."""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event

from .models import Membership, MembershipEvent, Organisation, OrganisationDeletionRequest


class OrganisationServiceError(ValidationError):
    """Expected validation failure in an organisation workflow."""


def _locked_actor_membership(*, actor: User, organisation: Organisation) -> Membership:
    try:
        membership = Membership.objects.select_for_update().get(
            organisation=organisation,
            user=actor,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("You are not an active member of this organisation.") from exc
    return membership


def _require_manager(*, actor: User, organisation: Organisation) -> Membership:
    membership = _locked_actor_membership(actor=actor, organisation=organisation)
    if not membership.can_manage_members:
        raise PermissionDenied("This action requires an owner or administrator role.")
    return membership


def _record_membership_event(
    *,
    actor: User,
    membership: Membership,
    kind: str,
    previous_role: str = "",
    new_role: str = "",
    previous_status: str = "",
    new_status: str = "",
    note: str = "",
) -> MembershipEvent:
    return MembershipEvent.objects.create(
        organisation=membership.organisation,
        membership_id_snapshot=membership.id,
        user=membership.user,
        actor=actor,
        kind=kind,
        previous_role=previous_role,
        new_role=new_role,
        previous_status=previous_status,
        new_status=new_status,
        note=note.strip(),
    )


def _require_owner(*, actor: User, organisation: Organisation) -> Membership:
    membership = _locked_actor_membership(actor=actor, organisation=organisation)
    if membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Only an organisation owner may perform this action.")
    return membership


def _require_active_organisation(organisation: Organisation) -> None:
    if organisation.status != Organisation.Status.ACTIVE:
        raise OrganisationServiceError(
            "Reactivate the organisation before making administrative changes."
        )


def _active_owner_count(*, organisation: Organisation) -> int:
    owner_ids = (
        Membership.objects.select_for_update()
        .filter(
            organisation=organisation,
            status=Membership.Status.ACTIVE,
            role=Membership.Role.OWNER,
        )
        .values_list("id", flat=True)
    )
    return len(list(owner_ids))


@transaction.atomic
def create_organisation(*, actor: User, name: str, slug: str) -> Organisation:
    """Create a tenant and make its creator the first owner atomically."""
    organisation = Organisation(name=name, slug=slug, created_by=actor)
    organisation.full_clean(validate_unique=False, validate_constraints=False)
    try:
        organisation.save()
    except IntegrityError as exc:
        raise OrganisationServiceError(
            "That organisation URL identifier is already in use."
        ) from exc
    membership = Membership.objects.create(
        organisation=organisation,
        user=actor,
        role=Membership.Role.OWNER,
        status=Membership.Status.ACTIVE,
    )
    _record_membership_event(
        actor=actor,
        membership=membership,
        kind=MembershipEvent.Kind.CREATED,
        new_role=membership.role,
        new_status=membership.status,
        note="Founding owner",
    )
    record_event(
        action="organisation.created",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={"name": organisation.name, "slug": organisation.slug},
    )
    from apps.workspaces.services import create_default_workspace

    create_default_workspace(organisation=organisation, actor=actor)

    from apps.billing.services import create_subscription_for_organisation

    create_subscription_for_organisation(organisation=organisation, actor=actor)
    return organisation


@transaction.atomic
def update_organisation(*, actor: User, organisation: Organisation, name: str) -> Organisation:
    """Update mutable organisation identity fields."""
    _require_manager(actor=actor, organisation=organisation)
    _require_active_organisation(organisation)
    previous_name = organisation.name
    organisation.name = name.strip()
    organisation.full_clean(exclude=["created_by"])
    organisation.save(update_fields=["name", "updated_at"])
    record_event(
        action="organisation.updated",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={"previous_name": previous_name, "name": organisation.name},
    )
    return organisation


@transaction.atomic
def add_membership(
    *,
    actor: User,
    organisation: Organisation,
    user: User,
    role: str,
) -> Membership:
    """Provision a membership for trusted internal workflows under explicit role rules."""
    actor_membership = _require_manager(actor=actor, organisation=organisation)
    _require_active_organisation(organisation)
    if role == Membership.Role.OWNER and actor_membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Only an owner may appoint another owner.")
    membership = Membership(
        organisation=organisation,
        user=user,
        role=role,
        status=Membership.Status.ACTIVE,
    )
    membership.full_clean(validate_unique=False, validate_constraints=False)
    try:
        membership.save()
    except IntegrityError as exc:
        raise OrganisationServiceError("That user is already a member.") from exc
    _record_membership_event(
        actor=actor,
        membership=membership,
        kind=MembershipEvent.Kind.CREATED,
        new_role=membership.role,
        new_status=membership.status,
    )
    record_event(
        action="membership.created",
        object_type="membership",
        object_id=str(membership.id),
        actor=actor,
        organisation=organisation,
        metadata={"user_id": str(user.id), "role": role},
    )
    return membership


@transaction.atomic
def change_membership_role(*, actor: User, membership: Membership, role: str) -> Membership:
    """Change a role while preserving at least one active owner."""
    membership = (
        Membership.objects.select_for_update()
        .select_related("organisation", "user")
        .get(id=membership.id)
    )
    actor_membership = _require_manager(actor=actor, organisation=membership.organisation)

    if membership.role == Membership.Role.OWNER and actor_membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Administrators cannot modify an owner.")
    if role == Membership.Role.OWNER and actor_membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Only an owner may appoint another owner.")
    if (
        membership.role == Membership.Role.OWNER
        and role != Membership.Role.OWNER
        and _active_owner_count(organisation=membership.organisation) <= 1
    ):
        raise OrganisationServiceError("An organisation must retain at least one active owner.")

    previous_role = membership.role
    membership.role = role
    membership.full_clean(validate_unique=False, validate_constraints=False)
    membership.save(update_fields=["role", "updated_at"])
    _record_membership_event(
        actor=actor,
        membership=membership,
        kind=MembershipEvent.Kind.ROLE_CHANGED,
        previous_role=previous_role,
        new_role=membership.role,
        previous_status=membership.status,
        new_status=membership.status,
    )
    record_event(
        action="membership.role_changed",
        object_type="membership",
        object_id=str(membership.id),
        actor=actor,
        organisation=membership.organisation,
        metadata={
            "user_id": str(membership.user_id),
            "previous_role": previous_role,
            "role": role,
        },
    )
    return membership


@transaction.atomic
def remove_membership(*, actor: User, membership: Membership) -> None:
    """Remove a member while preserving owner accountability."""
    membership = (
        Membership.objects.select_for_update()
        .select_related("organisation", "user")
        .get(id=membership.id)
    )
    actor_membership = _require_manager(actor=actor, organisation=membership.organisation)
    if membership.role == Membership.Role.OWNER:
        if actor_membership.role != Membership.Role.OWNER:
            raise PermissionDenied("Administrators cannot remove an owner.")
        if _active_owner_count(organisation=membership.organisation) <= 1:
            raise OrganisationServiceError("An organisation must retain at least one active owner.")

    from apps.decisions.models import Decision

    owns_open_decision = (
        Decision.objects.filter(
            organisation=membership.organisation,
            owner=membership.user,
        )
        .exclude(status=Decision.Status.ARCHIVED)
        .exists()
    )
    if owns_open_decision:
        raise OrganisationServiceError(
            "Transfer this member's unfinished decision ownership before removing access."
        )

    from apps.assumptions.models import Assumption

    owns_active_assumption = Assumption.objects.filter(
        organisation=membership.organisation,
        owner=membership.user,
        status=Assumption.Status.ACTIVE,
    ).exists()
    if owns_active_assumption:
        raise OrganisationServiceError(
            "Transfer this member's active assumption ownership before removing access."
        )

    from apps.risks.models import Risk

    owns_unclosed_risk = (
        Risk.objects.filter(
            organisation=membership.organisation,
            owner=membership.user,
        )
        .exclude(status=Risk.Status.CLOSED)
        .exists()
    )
    if owns_unclosed_risk:
        raise OrganisationServiceError(
            "Transfer this member's open risk ownership before removing access."
        )

    from apps.reviews.models import DecisionReview

    owns_active_implementation = (
        DecisionReview.objects.filter(
            organisation=membership.organisation,
            implementation_owner=membership.user,
        )
        .exclude(decision__status=Decision.Status.ARCHIVED)
        .exists()
    )
    if owns_active_implementation:
        raise OrganisationServiceError(
            "Transfer this member's active implementation ownership before removing access."
        )

    from apps.foresight.models import (
        Driver,
        FeedSubscription,
        ForesightCanvas,
        ResearchClaim,
        ScenarioSet,
        Signal,
        Signpost,
        StrategicImplication,
        Watchlist,
    )

    owns_active_feed = FeedSubscription.objects.filter(
        organisation=membership.organisation,
        owner=membership.user,
        is_active=True,
    ).exists()
    if owns_active_feed:
        raise OrganisationServiceError(
            "Transfer this member's active feed ownership before removing access."
        )

    owns_active_research_claim = ResearchClaim.objects.filter(
        organisation=membership.organisation,
        owner=membership.user,
        lifecycle_status=ResearchClaim.LifecycleStatus.ACTIVE,
    ).exists()
    if owns_active_research_claim:
        raise OrganisationServiceError(
            "Transfer this member's active research-claim ownership before removing access."
        )

    owns_active_signal = (
        Signal.objects.filter(
            organisation=membership.organisation,
            owner=membership.user,
        )
        .exclude(status=Signal.Status.RETIRED)
        .exists()
    )
    if owns_active_signal:
        raise OrganisationServiceError(
            "Transfer this member's active signal ownership before removing access."
        )

    owns_active_watchlist = Watchlist.objects.filter(
        organisation=membership.organisation,
        owner=membership.user,
        is_active=True,
    ).exists()
    if owns_active_watchlist:
        raise OrganisationServiceError(
            "Transfer this member's active watchlist ownership before removing access."
        )

    owns_active_canvas = (
        ForesightCanvas.objects.filter(organisation=membership.organisation, owner=membership.user)
        .exclude(status=ForesightCanvas.Status.ARCHIVED)
        .exists()
    )
    if owns_active_canvas:
        raise OrganisationServiceError(
            "Transfer this member's active foresight canvas ownership before removing access."
        )

    owns_active_driver = Driver.objects.filter(
        canvas__organisation=membership.organisation, owner=membership.user, is_active=True
    ).exists()
    if owns_active_driver:
        raise OrganisationServiceError(
            "Transfer this member's active driver ownership before removing access."
        )

    owns_open_implication = StrategicImplication.objects.filter(
        canvas__organisation=membership.organisation,
        owner=membership.user,
        status=StrategicImplication.Status.OPEN,
    ).exists()
    if owns_open_implication:
        raise OrganisationServiceError(
            "Transfer this member's open strategic implication ownership before removing access."
        )

    owns_active_scenario_set = (
        ScenarioSet.objects.filter(
            canvas__organisation=membership.organisation, owner=membership.user
        )
        .exclude(status=ScenarioSet.Status.ARCHIVED)
        .exists()
    )
    if owns_active_scenario_set:
        raise OrganisationServiceError(
            "Transfer this member's active scenario-set ownership before removing access."
        )

    owns_active_signpost = Signpost.objects.filter(
        scenario_set__canvas__organisation=membership.organisation,
        owner=membership.user,
        status=Signpost.Status.ACTIVE,
    ).exists()
    if owns_active_signpost:
        raise OrganisationServiceError(
            "Transfer this member's active signpost ownership before removing access."
        )

    from apps.contributions.models import ContributionRequest, FacilitationSession

    owns_active_contribution = (
        ContributionRequest.objects.filter(
            organisation=membership.organisation,
            assignee=membership.user,
        )
        .exclude(
            status__in=[ContributionRequest.Status.ACCEPTED, ContributionRequest.Status.CANCELLED]
        )
        .exists()
    )
    if owns_active_contribution:
        raise OrganisationServiceError(
            "Complete, cancel, or reassign this member's active contribution requests before removing access."
        )

    reviews_active_contribution = ContributionRequest.objects.filter(
        organisation=membership.organisation,
        reviewer=membership.user,
        status__in=[
            ContributionRequest.Status.SUBMITTED,
            ContributionRequest.Status.UNDER_REVIEW,
        ],
    ).exists()
    if reviews_active_contribution:
        raise OrganisationServiceError(
            "Complete or transfer this member's pending contribution reviews before removing access."
        )

    facilitates_active_session = (
        FacilitationSession.objects.filter(
            organisation=membership.organisation,
            facilitator=membership.user,
        )
        .exclude(
            status__in=[FacilitationSession.Status.CLOSED, FacilitationSession.Status.CANCELLED]
        )
        .exists()
    )
    if facilitates_active_session:
        raise OrganisationServiceError(
            "Transfer this member's active facilitation sessions before removing access."
        )

    from apps.evaluations.models import EvaluationExercise, PrioritisationPortfolio

    owns_active_evaluation = (
        EvaluationExercise.objects.filter(
            organisation=membership.organisation,
            owner=membership.user,
        )
        .exclude(status=EvaluationExercise.Status.ARCHIVED)
        .exists()
    )
    if owns_active_evaluation:
        raise OrganisationServiceError(
            "Transfer this member's active evaluation ownership before removing access."
        )

    owns_active_prioritisation = (
        PrioritisationPortfolio.objects.filter(
            organisation=membership.organisation,
            owner=membership.user,
        )
        .exclude(status=PrioritisationPortfolio.Status.ARCHIVED)
        .exists()
    )
    if owns_active_prioritisation:
        raise OrganisationServiceError(
            "Transfer this member's active prioritisation ownership before removing access."
        )

    from apps.decision_analysis.models import DecisionIssue
    from apps.decision_analysis.policies import WRITABLE_STATUSES

    owns_open_analysis_issue = DecisionIssue.objects.filter(
        organisation=membership.organisation,
        owner=membership.user,
        decision__status__in=WRITABLE_STATUSES,
        status__in=[DecisionIssue.Status.OPEN, DecisionIssue.Status.IN_PROGRESS],
    ).exists()
    if owns_open_analysis_issue:
        raise OrganisationServiceError(
            "Transfer this member's open decision-analysis issue ownership before removing access."
        )

    from apps.participants.services import (
        remove_non_owner_participations_for_member_departure,
    )

    removed_participation_count = remove_non_owner_participations_for_member_departure(
        actor=actor,
        organisation=membership.organisation,
        user=membership.user,
    )
    snapshot = {
        "user_id": str(membership.user_id),
        "role": membership.role,
        "membership_id": str(membership.id),
        "removed_participation_count": removed_participation_count,
    }
    organisation = membership.organisation
    _record_membership_event(
        actor=actor,
        membership=membership,
        kind=MembershipEvent.Kind.REMOVED,
        previous_role=membership.role,
        previous_status=membership.status,
        note="Membership removed",
    )
    membership.delete()
    record_event(
        action="membership.removed",
        object_type="membership",
        object_id=str(snapshot["membership_id"]),
        actor=actor,
        organisation=organisation,
        metadata=snapshot,
    )


@transaction.atomic
def update_organisation_administration(
    *, actor: User, organisation: Organisation, changes: dict
) -> Organisation:
    """Update profile, branding, invitation, and retention settings."""
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    membership = _require_manager(actor=actor, organisation=organisation)
    _require_active_organisation(organisation)
    owner_only = {"invitation_policy", "retention_days"}
    if owner_only.intersection(changes) and membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Only an owner may change invitation or retention policy.")
    before = {field: getattr(organisation, field) for field in changes}
    for field, value in changes.items():
        setattr(organisation, field, value)
    organisation.full_clean(exclude=["created_by", "deactivated_by"], validate_unique=False)
    organisation.save(update_fields=[*changes.keys(), "updated_at"])
    record_event(
        action="organisation.administration_updated",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "before": before,
            "after": {field: getattr(organisation, field) for field in changes},
        },
    )
    return organisation


@transaction.atomic
def transfer_organisation_ownership(
    *, actor: User, organisation: Organisation, target_membership: Membership, rationale: str
) -> tuple[Membership, Membership]:
    """Transfer accountable ownership and demote the acting owner to administrator."""
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    actor_membership = _require_owner(actor=actor, organisation=organisation)
    _require_active_organisation(organisation)
    target = (
        Membership.objects.select_for_update()
        .select_related("user", "organisation")
        .get(id=target_membership.id, organisation=organisation, status=Membership.Status.ACTIVE)
    )
    if target.user_id == actor.id:
        raise OrganisationServiceError("Choose another active member as the new owner.")
    rationale = rationale.strip()
    if len(rationale) < 10:
        raise OrganisationServiceError(
            {"rationale": "Record a meaningful ownership-transfer rationale."}
        )
    target_previous_role = target.role
    actor_membership.role = Membership.Role.ADMIN
    target.role = Membership.Role.OWNER
    actor_membership.save(update_fields=["role", "updated_at"])
    target.save(update_fields=["role", "updated_at"])
    _record_membership_event(
        actor=actor,
        membership=target,
        kind=MembershipEvent.Kind.OWNERSHIP_TRANSFERRED,
        previous_role=target_previous_role,
        new_role=Membership.Role.OWNER,
        previous_status=target.status,
        new_status=target.status,
        note=rationale,
    )
    _record_membership_event(
        actor=actor,
        membership=actor_membership,
        kind=MembershipEvent.Kind.ROLE_CHANGED,
        previous_role=Membership.Role.OWNER,
        new_role=Membership.Role.ADMIN,
        previous_status=actor_membership.status,
        new_status=actor_membership.status,
        note=f"Ownership transferred to {target.user.email}.",
    )
    record_event(
        action="organisation.ownership_transferred",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "new_owner_id": str(target.user_id),
            "previous_owner_id": str(actor.id),
            "rationale": rationale,
        },
    )
    return actor_membership, target


def organisation_deactivation_blockers(*, organisation: Organisation) -> list[str]:
    """Return explicit work that must be closed before administrative deactivation."""
    blockers: list[str] = []
    if organisation.decisions.exclude(status="archived").exists():
        blockers.append("Archive every active decision.")
    if organisation.invitations.filter(status="pending").exists():
        blockers.append("Revoke or resolve every pending invitation.")
    if organisation.contribution_requests.exclude(status__in=["accepted", "cancelled"]).exists():
        blockers.append("Complete or cancel active contribution requests.")
    if organisation.facilitation_sessions.exclude(status__in=["closed", "cancelled"]).exists():
        blockers.append("Close or cancel active facilitated sessions.")
    return blockers


@transaction.atomic
def deactivate_organisation(
    *, actor: User, organisation: Organisation, confirmation: str, reason: str
) -> Organisation:
    """Deactivate a tenant only after explicit owner confirmation and closure checks."""
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    _require_owner(actor=actor, organisation=organisation)
    if organisation.status == Organisation.Status.DEACTIVATED:
        raise OrganisationServiceError("The organisation is already deactivated.")
    if confirmation.strip() != organisation.name:
        raise OrganisationServiceError({"confirmation": "Enter the organisation name exactly."})
    reason = reason.strip()
    if len(reason) < 10:
        raise OrganisationServiceError(
            {"reason": "Record why the organisation is being deactivated."}
        )
    blockers = organisation_deactivation_blockers(organisation=organisation)
    if blockers:
        raise OrganisationServiceError({"blockers": blockers})
    organisation.status = Organisation.Status.DEACTIVATED
    organisation.deactivated_at = timezone.now()
    organisation.deactivated_by = actor
    organisation.full_clean(exclude=["created_by"], validate_unique=False)
    organisation.save(update_fields=["status", "deactivated_at", "deactivated_by", "updated_at"])
    record_event(
        action="organisation.deactivated",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={"reason": reason},
    )
    return organisation


@transaction.atomic
def reactivate_organisation(
    *, actor: User, organisation: Organisation, rationale: str
) -> Organisation:
    """Restore an administratively deactivated tenant under owner authority."""
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    _require_owner(actor=actor, organisation=organisation)
    if organisation.status != Organisation.Status.DEACTIVATED:
        raise OrganisationServiceError("The organisation is already active.")
    rationale = rationale.strip()
    if len(rationale) < 10:
        raise OrganisationServiceError(
            {"rationale": "Record why the organisation is being reactivated."}
        )
    organisation.status = Organisation.Status.ACTIVE
    organisation.deactivated_at = None
    organisation.deactivated_by = None
    organisation.save(update_fields=["status", "deactivated_at", "deactivated_by", "updated_at"])
    record_event(
        action="organisation.reactivated",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
        metadata={"rationale": rationale},
    )
    return organisation


@transaction.atomic
def request_organisation_deletion(
    *, actor: User, organisation: Organisation, confirmation: str, reason: str
) -> OrganisationDeletionRequest:
    """Create a delayed deletion request; no customer data is deleted automatically."""
    organisation = Organisation.objects.select_for_update().get(id=organisation.id)
    _require_owner(actor=actor, organisation=organisation)
    if organisation.status != Organisation.Status.DEACTIVATED:
        raise OrganisationServiceError("Deactivate the organisation before requesting deletion.")
    if confirmation.strip() != f"DELETE {organisation.name}":
        raise OrganisationServiceError(
            {"confirmation": f'Type "DELETE {organisation.name}" exactly.'}
        )
    reason = reason.strip()
    if len(reason) < 10:
        raise OrganisationServiceError({"reason": "Record a meaningful deletion reason."})
    if organisation.deletion_requests.filter(
        status=OrganisationDeletionRequest.Status.PENDING
    ).exists():
        raise OrganisationServiceError("A deletion request is already pending.")
    delay_days = max(30, organisation.retention_days or 30)
    request = OrganisationDeletionRequest.objects.create(
        organisation=organisation,
        requested_by=actor,
        reason=reason,
        earliest_deletion_at=timezone.now() + timedelta(days=delay_days),
    )
    record_event(
        action="organisation.deletion_requested",
        object_type="organisation_deletion_request",
        object_id=str(request.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "earliest_deletion_at": request.earliest_deletion_at.isoformat(),
            "reason": reason,
        },
    )
    return request


@transaction.atomic
def cancel_organisation_deletion(
    *, actor: User, deletion_request: OrganisationDeletionRequest, rationale: str
) -> OrganisationDeletionRequest:
    """Cancel a pending deletion request without erasing its administrative history."""
    item = (
        OrganisationDeletionRequest.objects.select_for_update()
        .select_related("organisation")
        .get(id=deletion_request.id)
    )
    _require_owner(actor=actor, organisation=item.organisation)
    if item.status != OrganisationDeletionRequest.Status.PENDING:
        raise OrganisationServiceError("Only a pending deletion request can be cancelled.")
    rationale = rationale.strip()
    if len(rationale) < 10:
        raise OrganisationServiceError({"rationale": "Record why deletion is being cancelled."})
    item.status = OrganisationDeletionRequest.Status.CANCELLED
    item.cancelled_by = actor
    item.cancelled_at = timezone.now()
    item.save(update_fields=["status", "cancelled_by", "cancelled_at", "updated_at"])
    record_event(
        action="organisation.deletion_cancelled",
        object_type="organisation_deletion_request",
        object_id=str(item.id),
        actor=actor,
        organisation=item.organisation,
        metadata={"rationale": rationale},
    )
    return item
