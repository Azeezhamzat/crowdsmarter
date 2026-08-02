import pytest
from django.urls import reverse

from apps.audit.models import AuditEvent
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_organisation_list_is_tenant_isolated(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    actor = user_factory()
    visible = organisation_factory(owner=actor, name="Visible", slug="visible")
    hidden = organisation_factory(name="Hidden", slug="hidden")
    api_client.force_authenticate(actor)

    response = api_client.get(reverse("organisations:list-create"))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(visible.id)]
    assert str(hidden.id) not in response.content.decode()


@pytest.mark.django_db
def test_create_retrieve_and_update_organisation(
    api_client, user_factory
):  # type: ignore[no-untyped-def]
    actor = user_factory()
    api_client.force_authenticate(actor)

    create_response = api_client.post(
        reverse("organisations:list-create"),
        {"name": "Acme", "slug": "acme"},
        format="json",
    )
    assert create_response.status_code == 201
    organisation_id = create_response.json()["id"]
    assert create_response.json()["current_user_role"] == "owner"

    detail_url = reverse("organisations:detail", kwargs={"organisation_id": organisation_id})
    assert api_client.get(detail_url).status_code == 200

    update_response = api_client.patch(detail_url, {"name": "Acme Group"}, format="json")
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Acme Group"
    assert AuditEvent.objects.filter(action="organisation.updated").exists()


@pytest.mark.django_db
def test_outsider_receives_not_found_for_other_tenant(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    outsider = user_factory()
    organisation = organisation_factory()
    api_client.force_authenticate(outsider)

    response = api_client.get(
        reverse("organisations:detail", kwargs={"organisation_id": organisation.id})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_contributor_can_read_but_cannot_update_organisation(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(contributor)
    url = reverse("organisations:detail", kwargs={"organisation_id": organisation.id})

    assert api_client.get(url).status_code == 200
    assert api_client.patch(url, {"name": "Not allowed"}, format="json").status_code == 403


@pytest.mark.django_db
def test_owner_can_list_change_and_remove_accepted_member(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    member = user_factory(email="new@example.com")
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=member,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(owner)
    collection_url = reverse(
        "organisations:membership-list",
        kwargs={"organisation_id": organisation.id},
    )

    list_response = api_client.get(collection_url)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2
    assert api_client.post(
        collection_url,
        {"email": "bypass@example.com", "role": "contributor"},
        format="json",
    ).status_code == 405

    detail_url = reverse(
        "organisations:membership-detail",
        kwargs={"membership_id": membership.id},
    )
    patch_response = api_client.patch(detail_url, {"role": "viewer"}, format="json")
    assert patch_response.status_code == 200
    assert patch_response.json()["role"] == "viewer"

    delete_response = api_client.delete(detail_url)
    assert delete_response.status_code == 204
    assert not Membership.objects.filter(id=membership.id).exists()


@pytest.mark.django_db
def test_membership_collection_never_accepts_direct_additions(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse(
            "organisations:membership-list",
            kwargs={"organisation_id": organisation.id},
        ),
        {"email": "candidate@example.com", "role": "viewer"},
        format="json",
    )
    assert response.status_code == 405


@pytest.mark.django_db
def test_admin_cannot_patch_owner_membership(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    admin = user_factory()
    organisation = organisation_factory(owner=owner)
    owner_membership = Membership.objects.get(organisation=organisation, user=owner)
    Membership.objects.create(
        organisation=organisation,
        user=admin,
        role=Membership.Role.ADMIN,
    )
    api_client.force_authenticate(admin)

    response = api_client.patch(
        reverse(
            "organisations:membership-detail",
            kwargs={"membership_id": owner_membership.id},
        ),
        {"role": "viewer"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_last_owner_rule_returns_validation_response(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    owner_membership = Membership.objects.get(organisation=organisation, user=owner)
    api_client.force_authenticate(owner)

    response = api_client.delete(
        reverse(
            "organisations:membership-detail",
            kwargs={"membership_id": owner_membership.id},
        )
    )
    assert response.status_code == 400
    assert "retain at least one" in str(response.json())


@pytest.mark.django_db
def test_suspended_membership_grants_no_tenant_visibility(
    api_client, user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    suspended_user = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=suspended_user,
        role=Membership.Role.VIEWER,
        status=Membership.Status.SUSPENDED,
    )
    api_client.force_authenticate(suspended_user)

    assert api_client.get(reverse("organisations:list-create")).json() == []
    detail = api_client.get(
        reverse("organisations:detail", kwargs={"organisation_id": organisation.id})
    )
    assert detail.status_code == 404
