"""Transactional organisation and membership workflows."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.audit.services import record_event

from .models import Membership, Organisation


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


def _active_owner_count(*, organisation: Organisation) -> int:
    owner_ids = Membership.objects.select_for_update().filter(
        organisation=organisation,
        status=Membership.Status.ACTIVE,
        role=Membership.Role.OWNER,
    ).values_list("id", flat=True)
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
    Membership.objects.create(
        organisation=organisation,
        user=actor,
        role=Membership.Role.OWNER,
        status=Membership.Status.ACTIVE,
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
    return organisation


@transaction.atomic
def update_organisation(*, actor: User, organisation: Organisation, name: str) -> Organisation:
    """Update mutable organisation identity fields."""
    _require_manager(actor=actor, organisation=organisation)
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
    membership = Membership.objects.select_for_update().select_related("organisation", "user").get(
        id=membership.id
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
    membership = Membership.objects.select_for_update().select_related("organisation", "user").get(
        id=membership.id
    )
    actor_membership = _require_manager(actor=actor, organisation=membership.organisation)
    if membership.role == Membership.Role.OWNER:
        if actor_membership.role != Membership.Role.OWNER:
            raise PermissionDenied("Administrators cannot remove an owner.")
        if _active_owner_count(organisation=membership.organisation) <= 1:
            raise OrganisationServiceError("An organisation must retain at least one active owner.")

    from apps.decisions.models import Decision

    owns_open_decision = Decision.objects.filter(
        organisation=membership.organisation,
        owner=membership.user,
    ).exclude(status=Decision.Status.ARCHIVED).exists()
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

    owns_active_implementation = DecisionReview.objects.filter(
        organisation=membership.organisation,
        implementation_owner=membership.user,
    ).exclude(decision__status=Decision.Status.ARCHIVED).exists()
    if owns_active_implementation:
        raise OrganisationServiceError(
            "Transfer this member's active implementation ownership before removing access."
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
    membership.delete()
    record_event(
        action="membership.removed",
        object_type="membership",
        object_id=snapshot["membership_id"],
        actor=actor,
        organisation=organisation,
        metadata=snapshot,
    )
