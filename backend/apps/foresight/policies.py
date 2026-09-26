"""Authorisation policies for foresight records."""

from apps.organisations.models import Membership


def membership_for(actor, organisation):  # type: ignore[no-untyped-def]
    return organisation.memberships.filter(user=actor, status=Membership.Status.ACTIVE).first()


def can_contribute(*, actor, organisation) -> bool:  # type: ignore[no-untyped-def]
    membership = membership_for(actor, organisation)
    return bool(
        membership
        and membership.role
        in {Membership.Role.OWNER, Membership.Role.ADMIN, Membership.Role.CONTRIBUTOR}
    )


def can_manage_record(*, actor, organisation, created_by_id=None, owner_id=None) -> bool:  # type: ignore[no-untyped-def]
    membership = membership_for(actor, organisation)
    if membership is None:
        return False
    if membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        return True
    return membership.role == Membership.Role.CONTRIBUTOR and actor.id in {
        created_by_id,
        owner_id,
    }
