"""Platform-administrator command behaviour."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.organisations.models import Membership
from apps.platform_admin.models import PlatformAdministrator


@pytest.mark.django_db
def test_command_grants_explicit_capability_without_hidden_membership(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    user = user_factory(email="hello@crowdsmarter.com", is_staff=False, is_superuser=False)
    organisation_factory(name="Real client", slug="real-client")

    output = StringIO()
    call_command("ensure_platform_admin", email=user.email, stdout=output)

    user.refresh_from_db()
    assert user.is_staff is False
    assert user.is_superuser is False
    assert PlatformAdministrator.objects.filter(
        user=user, status=PlatformAdministrator.Status.ACTIVE
    ).exists()
    assert Membership.objects.filter(user=user).count() == 0
    assert "APPLIED" in output.getvalue()


@pytest.mark.django_db
def test_command_can_grant_technical_flags_and_demo_memberships_only(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    user = user_factory(email="hello@crowdsmarter.com", is_staff=False, is_superuser=False)
    demo = organisation_factory(name="NorthStar Grid Services", slug="northstar-grid-services-sim")
    real = organisation_factory(name="Real client", slug="real-client")

    call_command(
        "ensure_platform_admin",
        email=user.email,
        demo_organisations=True,
        technical_admin=True,
    )

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.is_superuser is True
    assert Membership.objects.filter(
        user=user,
        organisation=demo,
        role=Membership.Role.OWNER,
        status=Membership.Status.ACTIVE,
    ).exists()
    assert not Membership.objects.filter(user=user, organisation=real).exists()


@pytest.mark.django_db
def test_command_dry_run_rolls_back_all_changes(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="hello@crowdsmarter.com", is_staff=False, is_superuser=False)
    organisation_factory(name="NorthStar Grid Services", slug="northstar-grid-services-sim")

    call_command(
        "ensure_platform_admin",
        email=user.email,
        demo_organisations=True,
        technical_admin=True,
        dry_run=True,
    )

    user.refresh_from_db()
    assert user.is_staff is False
    assert user.is_superuser is False
    assert PlatformAdministrator.objects.filter(user=user).count() == 0
    assert Membership.objects.filter(user=user).count() == 0


@pytest.mark.django_db
def test_command_refuses_to_create_an_unknown_admin_account():
    with pytest.raises(CommandError, match="No CrowdSmarter account exists"):
        call_command("ensure_platform_admin", email="missing@crowdsmarter.com")
