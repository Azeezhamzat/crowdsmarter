from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.billing.models import OrganisationSubscription, Plan


@pytest.fixture
def plan(db):  # type: ignore[no-untyped-def]
    return Plan.objects.create(key="model-test-plan", name="Model Test Plan")


@pytest.mark.django_db
def test_plan_str_is_its_name(plan):  # type: ignore[no-untyped-def]
    assert str(plan) == "Model Test Plan"


@pytest.mark.django_db
def test_plan_clean_normalises_key_and_name(db):  # type: ignore[no-untyped-def]
    p = Plan(key="  Team  ", name="  Team  ", description="  x  ")
    p.clean()
    assert p.key == "team"
    assert p.name == "Team"
    assert p.description == "x"


@pytest.mark.django_db
def test_subscription_str(organisation_factory, plan, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    subscription = OrganisationSubscription.objects.create(
        organisation=organisation, plan=plan, created_by=organisation.created_by
    )
    assert str(subscription) == f"{organisation.name}: Model Test Plan (trialing)"


@pytest.mark.django_db
def test_is_trial_expired(organisation_factory, plan):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    active = OrganisationSubscription.objects.create(
        organisation=organisation,
        plan=plan,
        created_by=organisation.created_by,
        trial_ends_at=timezone.now() - timedelta(days=1),
    )
    assert active.is_trial_expired is True

    active.trial_ends_at = timezone.now() + timedelta(days=1)
    assert active.is_trial_expired is False

    active.status = OrganisationSubscription.Status.ACTIVE
    active.trial_ends_at = timezone.now() - timedelta(days=1)
    assert active.is_trial_expired is False


@pytest.mark.django_db
def test_billing_contact_must_be_active_member(organisation_factory, plan, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    outsider = user_factory()
    subscription = OrganisationSubscription(
        organisation=organisation,
        plan=plan,
        created_by=organisation.created_by,
        billing_contact=outsider,
    )
    with pytest.raises(ValidationError, match="active organisation member"):
        subscription.clean()

    subscription.billing_contact = organisation.created_by
    subscription.clean()
