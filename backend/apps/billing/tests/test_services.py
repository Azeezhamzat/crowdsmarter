import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.billing.models import OrganisationSubscription, Plan
from apps.billing.services import (
    BillingServiceError,
    assert_can_add_member,
    assert_can_create_decision,
    change_plan,
    create_subscription_for_organisation,
    default_plan,
    set_billing_contact,
)
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_default_plan_returns_lowest_order_active_plan():  # type: ignore[no-untyped-def]
    plan = default_plan()
    assert plan.key == "team"


@pytest.mark.django_db
def test_default_plan_raises_when_none_configured():  # type: ignore[no-untyped-def]
    Plan.objects.update(is_active=False)
    with pytest.raises(BillingServiceError, match="No active plan"):
        default_plan()


@pytest.mark.django_db
def test_create_subscription_for_organisation_enrolls_default_plan_trial(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    OrganisationSubscription.objects.filter(organisation=organisation).delete()

    subscription = create_subscription_for_organisation(
        organisation=organisation, actor=organisation.created_by
    )

    assert subscription.plan.key == "team"
    assert subscription.status == OrganisationSubscription.Status.TRIALING
    assert subscription.trial_ends_at is not None
    assert AuditEvent.objects.filter(
        organisation=organisation, action="billing.subscription_started"
    ).exists()


@pytest.mark.django_db
def test_change_plan_requires_owner(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    member = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=member,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )

    with pytest.raises(PermissionDenied):
        change_plan(actor=member, organisation=organisation, plan_key="professional")


@pytest.mark.django_db
def test_change_plan_rejects_unknown_key(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    with pytest.raises(BillingServiceError):
        change_plan(
            actor=organisation.created_by, organisation=organisation, plan_key="does-not-exist"
        )


@pytest.mark.django_db
def test_change_plan_switches_plan_and_audits(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    create_subscription_for_organisation(organisation=organisation, actor=organisation.created_by)

    subscription = change_plan(
        actor=organisation.created_by, organisation=organisation, plan_key="professional"
    )

    assert subscription.plan.key == "professional"
    assert subscription.status == OrganisationSubscription.Status.ACTIVE
    assert AuditEvent.objects.filter(
        organisation=organisation, action="billing.plan_changed"
    ).exists()


@pytest.mark.django_db
def test_set_billing_contact_requires_owner(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    member = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=member,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )

    with pytest.raises(PermissionDenied):
        set_billing_contact(actor=member, organisation=organisation, user_id=member.id)


@pytest.mark.django_db
def test_set_billing_contact_updates_and_audits(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    create_subscription_for_organisation(organisation=organisation, actor=owner)

    subscription = set_billing_contact(actor=owner, organisation=organisation, user_id=owner.id)

    assert subscription.billing_contact_id == owner.id
    assert AuditEvent.objects.filter(
        organisation=organisation, action="billing.billing_contact_changed"
    ).exists()


@pytest.mark.django_db
def test_assert_can_create_decision_noop_without_subscription(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    OrganisationSubscription.objects.filter(organisation=organisation).delete()

    assert_can_create_decision(organisation=organisation)


@pytest.mark.django_db
def test_assert_can_create_decision_noop_when_unlimited(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    subscription = create_subscription_for_organisation(
        organisation=organisation, actor=organisation.created_by
    )
    subscription.plan.max_active_decisions = None
    subscription.plan.save(update_fields=["max_active_decisions"])

    assert_can_create_decision(organisation=organisation)


@pytest.mark.django_db
def test_assert_can_create_decision_raises_once_limit_reached(
    organisation_factory, workspace_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    subscription = create_subscription_for_organisation(
        organisation=organisation, actor=organisation.created_by
    )
    low_limit_plan = Plan.objects.create(
        key="low-limit-test-plan", name="Low limit test plan", max_active_decisions=1
    )
    subscription.plan = low_limit_plan
    subscription.save(update_fields=["plan"])

    workspace = workspace_factory(organisation=organisation)
    assert_can_create_decision(organisation=organisation)

    decision_factory(workspace=workspace)

    with pytest.raises(BillingServiceError, match="active decisions"):
        assert_can_create_decision(organisation=organisation)


@pytest.mark.django_db
def test_assert_can_create_decision_excludes_archived(
    organisation_factory, workspace_factory, decision_factory
):  # type: ignore[no-untyped-def]
    from apps.decisions.models import Decision

    organisation = organisation_factory()
    subscription = create_subscription_for_organisation(
        organisation=organisation, actor=organisation.created_by
    )
    low_limit_plan = Plan.objects.create(
        key="low-limit-test-plan", name="Low limit test plan", max_active_decisions=1
    )
    subscription.plan = low_limit_plan
    subscription.save(update_fields=["plan"])

    workspace = workspace_factory(organisation=organisation)
    decision_factory(workspace=workspace, status=Decision.Status.ARCHIVED)

    assert_can_create_decision(organisation=organisation)


@pytest.mark.django_db
def test_assert_can_add_member_noop_without_subscription(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    OrganisationSubscription.objects.filter(organisation=organisation).delete()

    assert_can_add_member(organisation=organisation)


@pytest.mark.django_db
def test_assert_can_add_member_raises_once_limit_reached(
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    subscription = create_subscription_for_organisation(
        organisation=organisation, actor=organisation.created_by
    )
    low_limit_plan = Plan.objects.create(
        key="low-limit-member-plan", name="Low limit member plan", max_active_members=1
    )
    subscription.plan = low_limit_plan
    subscription.save(update_fields=["plan"])

    with pytest.raises(BillingServiceError, match="active members"):
        assert_can_add_member(organisation=organisation)
