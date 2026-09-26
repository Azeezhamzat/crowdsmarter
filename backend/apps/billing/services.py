"""Plan-entitlement enforcement and subscription workflows. No payment
processing lives here - see ADR 0031."""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.organisations.models import Membership, Organisation

from .models import OrganisationSubscription, Plan


class BillingServiceError(ValidationError):
    """Expected billing/entitlement workflow failure."""


def _active_membership(*, actor: User, organisation: Organisation) -> Membership:
    try:
        return Membership.objects.get(
            organisation=organisation, user=actor, status=Membership.Status.ACTIVE
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("You are not an active member of this organisation.") from exc


def _require_owner(*, actor: User, organisation: Organisation) -> Membership:
    membership = _active_membership(actor=actor, organisation=organisation)
    if membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Only an organisation owner may perform this action.")
    return membership


def default_plan() -> Plan:
    plan = Plan.objects.filter(is_active=True).order_by("order").first()
    if plan is None:
        raise BillingServiceError("No active plan is configured. Contact support.")
    return plan


@transaction.atomic
def create_subscription_for_organisation(
    *, organisation: Organisation, actor: User
) -> OrganisationSubscription:
    """Auto-enroll a newly created organisation in the default plan's trial."""
    plan = default_plan()
    trial_ends_at = timezone.now() + timedelta(days=plan.trial_days) if plan.trial_days else None
    subscription = OrganisationSubscription(
        organisation=organisation,
        plan=plan,
        status=OrganisationSubscription.Status.TRIALING,
        trial_ends_at=trial_ends_at,
        created_by=actor,
    )
    subscription.full_clean(validate_unique=False, validate_constraints=False)
    subscription.save()
    record_event(
        action="billing.subscription_started",
        object_type="organisation_subscription",
        object_id=str(subscription.id),
        actor=actor,
        organisation=organisation,
        metadata={"plan_key": plan.key},
    )
    return subscription


@transaction.atomic
def change_plan(
    *, actor: User, organisation: Organisation, plan_key: str
) -> OrganisationSubscription:
    """Record a self-service or admin-assisted plan change (no payment collected)."""
    _require_owner(actor=actor, organisation=organisation)
    try:
        plan = Plan.objects.get(key=plan_key, is_active=True)
    except Plan.DoesNotExist as exc:
        raise BillingServiceError({"plan_key": "Choose an available plan."}) from exc
    subscription = OrganisationSubscription.objects.select_for_update().get(
        organisation=organisation
    )
    previous_plan_key = subscription.plan.key
    subscription.plan = plan
    subscription.status = OrganisationSubscription.Status.ACTIVE
    subscription.full_clean(validate_unique=False, validate_constraints=False)
    subscription.save(update_fields=["plan", "status", "updated_at"])
    record_event(
        action="billing.plan_changed",
        object_type="organisation_subscription",
        object_id=str(subscription.id),
        actor=actor,
        organisation=organisation,
        metadata={"previous_plan_key": previous_plan_key, "new_plan_key": plan.key},
    )
    return subscription


@transaction.atomic
def set_billing_contact(
    *, actor: User, organisation: Organisation, user_id
) -> OrganisationSubscription:
    _require_owner(actor=actor, organisation=organisation)
    subscription = OrganisationSubscription.objects.select_for_update().get(
        organisation=organisation
    )
    subscription.billing_contact_id = user_id
    subscription.full_clean(validate_unique=False, validate_constraints=False)
    subscription.save(update_fields=["billing_contact", "updated_at"])
    record_event(
        action="billing.billing_contact_changed",
        object_type="organisation_subscription",
        object_id=str(subscription.id),
        actor=actor,
        organisation=organisation,
        metadata={"billing_contact_id": str(user_id) if user_id else None},
    )
    return subscription


def assert_can_create_decision(*, organisation: Organisation) -> None:
    """Raise if creating one more active decision would exceed the plan limit."""
    from apps.decisions.models import Decision

    subscription = (
        OrganisationSubscription.objects.select_related("plan")
        .filter(organisation=organisation)
        .first()
    )
    if subscription is None or subscription.plan.max_active_decisions is None:
        return
    active_count = (
        Decision.objects.filter(organisation=organisation)
        .exclude(status=Decision.Status.ARCHIVED)
        .count()
    )
    if active_count >= subscription.plan.max_active_decisions:
        raise BillingServiceError(
            f"This organisation's {subscription.plan.name} plan allows up to "
            f"{subscription.plan.max_active_decisions} active decisions. Archive an "
            "existing decision or change plans before creating another."
        )


def assert_can_add_member(*, organisation: Organisation) -> None:
    """Raise if adding one more active member would exceed the plan limit."""
    subscription = (
        OrganisationSubscription.objects.select_related("plan")
        .filter(organisation=organisation)
        .first()
    )
    if subscription is None or subscription.plan.max_active_members is None:
        return
    active_count = Membership.objects.filter(
        organisation=organisation, status=Membership.Status.ACTIVE
    ).count()
    if active_count >= subscription.plan.max_active_members:
        raise BillingServiceError(
            f"This organisation's {subscription.plan.name} plan allows up to "
            f"{subscription.plan.max_active_members} active members. Remove a member "
            "or change plans before adding another."
        )
