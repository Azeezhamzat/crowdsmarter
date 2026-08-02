"""Organisation-method permission rules."""

from apps.organisations.models import Membership


def active_membership(*, actor, organisation):  # type: ignore[no-untyped-def]
    return Membership.objects.filter(
        organisation=organisation, user=actor, status=Membership.Status.ACTIVE
    ).first()


def can_manage_methods(*, actor, organisation) -> bool:  # type: ignore[no-untyped-def]
    membership = active_membership(actor=actor, organisation=organisation)
    return bool(membership and membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN})


def can_approve_methods(*, actor, organisation) -> bool:  # type: ignore[no-untyped-def]
    membership = active_membership(actor=actor, organisation=organisation)
    return bool(membership and membership.role == Membership.Role.OWNER)
