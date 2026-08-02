import pytest
from django.urls import reverse

from apps.organisations.models import Membership, MembershipEvent, Organisation


@pytest.mark.django_db
def test_owner_updates_policy_and_admin_cannot_change_owner_only_settings(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory(email="governance-owner@example.com")
    admin = user_factory(email="governance-admin@example.com")
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(organisation=organisation, user=admin, role=Membership.Role.ADMIN)
    url = reverse("organisations:administration", kwargs={"organisation_id": organisation.id})

    api_client.force_authenticate(admin)
    assert api_client.patch(url, {"brand_name": "Crowd Unit"}, format="json").status_code == 200
    denied = api_client.patch(url, {"invitation_policy": "owners_only"}, format="json")
    assert denied.status_code == 403

    api_client.force_authenticate(owner)
    updated = api_client.patch(
        url,
        {"invitation_policy": "owners_only", "retention_days": 60, "primary_colour": "#123456"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["retention_days"] == 60


@pytest.mark.django_db
def test_ownership_transfer_is_attributable_and_preserves_an_owner(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory(email="old-owner@example.com")
    successor = user_factory(email="new-owner@example.com")
    organisation = organisation_factory(owner=owner)
    target = Membership.objects.create(
        organisation=organisation, user=successor, role=Membership.Role.ADMIN
    )
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("organisations:transfer-ownership", kwargs={"organisation_id": organisation.id}),
        {"target_membership_id": str(target.id), "rationale": "Leadership accountability has formally changed."},
        format="json",
    )
    assert response.status_code == 200
    assert Membership.objects.get(organisation=organisation, user=successor).role == Membership.Role.OWNER
    assert Membership.objects.get(organisation=organisation, user=owner).role == Membership.Role.ADMIN
    assert MembershipEvent.objects.filter(
        organisation=organisation, kind=MembershipEvent.Kind.OWNERSHIP_TRANSFERRED
    ).exists()


@pytest.mark.django_db
def test_deletion_history_is_owner_only(api_client, organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    owner = user_factory(email="deletion-owner@example.com")
    contributor = user_factory(email="deletion-contributor@example.com")
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation, user=contributor, role=Membership.Role.CONTRIBUTOR
    )
    url = reverse("organisations:deletion-requests", kwargs={"organisation_id": organisation.id})
    api_client.force_authenticate(contributor)
    assert api_client.get(url).status_code == 403


@pytest.mark.django_db
def test_deactivated_organisation_cannot_create_new_method(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory(email="inactive-method-owner@example.com")
    organisation = organisation_factory(owner=owner)
    Organisation.objects.filter(id=organisation.id).update(
        status=Organisation.Status.DEACTIVATED,
        deactivated_at="2026-08-01T12:00:00Z",
        deactivated_by=owner,
    )
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("methodology:method-clone", kwargs={"organisation_id": organisation.id}),
        {"builtin_key": "technology_adoption"},
        format="json",
    )
    assert response.status_code == 400
