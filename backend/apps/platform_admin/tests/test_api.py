from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.organisations.models import Membership
from apps.platform_admin.models import PlatformAdministrator, SupportAccessGrant


def grant_platform_capability(user, rationale="Responsible for CrowdSmarter tenant operations."):
    return PlatformAdministrator.objects.create(
        user=user,
        rationale=rationale,
        status=PlatformAdministrator.Status.ACTIVE,
    )


@pytest.mark.django_db
def test_django_superuser_flag_does_not_replace_platform_capability(api_client, user_factory):
    user = user_factory(is_staff=True, is_superuser=True)
    api_client.force_authenticate(user)

    response = api_client.get(reverse("platform_admin:platform-admin-overview"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_platform_administrator_can_open_overview_without_tenant_membership(
    api_client, user_factory, organisation_factory
):
    administrator = user_factory(email="hello@crowdsmarter.com")
    organisation = organisation_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.get(reverse("platform_admin:platform-admin-overview"))

    assert response.status_code == 200
    assert response.json()["counts"]["organisations"] == 1
    assert not Membership.objects.filter(organisation=organisation, user=administrator).exists()


@pytest.mark.django_db
def test_tenant_detail_requires_reasoned_support_access_and_does_not_create_membership(
    api_client, user_factory, organisation_factory
):
    administrator = user_factory(email="hello@crowdsmarter.com")
    organisation = organisation_factory()
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)
    detail_url = reverse(
        "platform_admin:platform-admin-organisation-detail",
        kwargs={"organisation_id": organisation.id},
    )

    assert api_client.get(detail_url).status_code == 403

    grant_response = api_client.post(
        reverse(
            "platform_admin:platform-admin-support-access-create",
            kwargs={"organisation_id": organisation.id},
        ),
        {
            "access_level": "read_only",
            "duration_hours": 2,
            "reason": "Customer requested investigation of organisation access visibility.",
        },
        format="json",
    )
    assert grant_response.status_code == 201
    assert api_client.get(detail_url).status_code == 200
    assert not Membership.objects.filter(organisation=organisation, user=administrator).exists()
    assert AuditEvent.objects.filter(action="platform_support_access.granted").exists()


@pytest.mark.django_db
def test_read_only_support_cannot_transfer_ownership(
    api_client, user_factory, organisation_factory
):
    administrator = user_factory(email="hello@crowdsmarter.com")
    owner = user_factory(email="owner@example.com")
    candidate = user_factory(email="candidate@example.com")
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=candidate,
        role=Membership.Role.ADMIN,
        status=Membership.Status.ACTIVE,
    )
    grant_platform_capability(administrator)
    SupportAccessGrant.objects.create(
        administrator=administrator,
        organisation=organisation,
        access_level=SupportAccessGrant.AccessLevel.READ_ONLY,
        reason="Reviewing customer ownership information after a support request.",
        expires_at=timezone.now() + timedelta(hours=2),
    )
    api_client.force_authenticate(administrator)

    response = api_client.post(
        reverse(
            "platform_admin:platform-admin-organisation-ownership",
            kwargs={"organisation_id": organisation.id},
        ),
        {
            "target_membership_id": str(membership.id),
            "rationale": "Customer leadership approved an accountable ownership transfer.",
            "demote_existing_owners": True,
            "confirmation": organisation.name,
        },
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_operational_support_transfers_ownership_without_joining_tenant(
    api_client, user_factory, organisation_factory
):
    administrator = user_factory(email="hello@crowdsmarter.com")
    owner = user_factory(email="owner@example.com")
    candidate = user_factory(email="candidate@example.com")
    organisation = organisation_factory(owner=owner)
    candidate_membership = Membership.objects.create(
        organisation=organisation,
        user=candidate,
        role=Membership.Role.ADMIN,
        status=Membership.Status.ACTIVE,
    )
    grant_platform_capability(administrator)
    SupportAccessGrant.objects.create(
        administrator=administrator,
        organisation=organisation,
        access_level=SupportAccessGrant.AccessLevel.OPERATIONAL,
        reason="Customer requested an urgent accountable ownership transfer.",
        expires_at=timezone.now() + timedelta(hours=2),
    )
    api_client.force_authenticate(administrator)

    response = api_client.post(
        reverse(
            "platform_admin:platform-admin-organisation-ownership",
            kwargs={"organisation_id": organisation.id},
        ),
        {
            "target_membership_id": str(candidate_membership.id),
            "rationale": "Customer leadership approved candidate as the new accountable owner.",
            "demote_existing_owners": True,
            "confirmation": organisation.name,
        },
        format="json",
    )

    assert response.status_code == 200
    candidate_membership.refresh_from_db()
    assert candidate_membership.role == Membership.Role.OWNER
    assert Membership.objects.get(organisation=organisation, user=owner).role == Membership.Role.ADMIN
    assert not Membership.objects.filter(organisation=organisation, user=administrator).exists()
    assert AuditEvent.objects.filter(action="platform_organisation.ownership_transferred").exists()


@pytest.mark.django_db
def test_platform_administrator_cannot_suspend_own_account(api_client, user_factory):
    administrator = user_factory(email="hello@crowdsmarter.com")
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.post(
        reverse(
            "platform_admin:platform-admin-user-state",
            kwargs={"user_id": administrator.id},
        ),
        {
            "is_active": False,
            "rationale": "Attempt to suspend the currently authenticated platform operator.",
        },
        format="json",
    )

    assert response.status_code == 400
    administrator.refresh_from_db()
    assert administrator.is_active is True


@pytest.mark.django_db
def test_platform_configuration_update_is_audited(api_client, user_factory):
    administrator = user_factory(email="hello@crowdsmarter.com")
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.patch(
        reverse("platform_admin:platform-admin-configuration"),
        {
            "public_contact_email": "hello@crowdsmarter.com",
            "demo_email": "demos@crowdsmarter.com",
            "support_email": "support@crowdsmarter.com",
            "privacy_email": "privacy@crowdsmarter.com",
            "security_email": "security@crowdsmarter.com",
            "notification_sender_email": "notifications@crowdsmarter.com",
            "support_access_max_hours": 12,
            "rationale": "Introduce role-specific aliases while retaining central inbox routing.",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["support_email"] == "support@crowdsmarter.com"
    assert AuditEvent.objects.filter(action="platform_configuration.updated").exists()


@pytest.mark.django_db
def test_platform_administrator_cannot_suspend_a_sole_tenant_owner(
    api_client, user_factory, organisation_factory
):
    administrator = user_factory(email="hello@crowdsmarter.com")
    owner = user_factory(email="sole.owner@example.com")
    organisation_factory(owner=owner)
    grant_platform_capability(administrator)
    api_client.force_authenticate(administrator)

    response = api_client.post(
        reverse(
            "platform_admin:platform-admin-user-state",
            kwargs={"user_id": owner.id},
        ),
        {
            "is_active": False,
            "rationale": "Security review requires account suspension after ownership continuity is secured.",
        },
        format="json",
    )

    assert response.status_code == 400
    owner.refresh_from_db()
    assert owner.is_active is True
