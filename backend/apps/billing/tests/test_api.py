import pytest
from django.urls import reverse

from apps.billing.models import OrganisationSubscription
from apps.billing.services import create_subscription_for_organisation
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_plan_list_is_visible_to_any_authenticated_user(
    api_client, user_factory
):  # type: ignore[no-untyped-def]
    api_client.force_authenticate(user_factory())

    response = api_client.get(reverse("billing:plans"))

    assert response.status_code == 200
    keys = {plan["key"] for plan in response.json()}
    assert {"team", "professional", "enterprise"}.issubset(keys)


@pytest.mark.django_db
def test_subscription_view_returns_404_for_non_member(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())

    response = api_client.get(
        reverse("billing:subscription", kwargs={"organisation_id": organisation.id})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_subscription_view_returns_plan_and_usage_for_member(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    create_subscription_for_organisation(organisation=organisation, actor=organisation.created_by)
    api_client.force_authenticate(organisation.created_by)

    response = api_client.get(
        reverse("billing:subscription", kwargs={"organisation_id": organisation.id})
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["key"] == "team"
    assert body["active_member_count"] == 1
    assert body["active_decision_count"] == 0


@pytest.mark.django_db
def test_change_plan_via_api_requires_owner(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    create_subscription_for_organisation(organisation=organisation, actor=organisation.created_by)
    member = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=member,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    api_client.force_authenticate(member)

    response = api_client.post(
        reverse("billing:change-plan", kwargs={"organisation_id": organisation.id}),
        {"plan_key": "professional"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_change_plan_via_api_as_owner(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    create_subscription_for_organisation(organisation=organisation, actor=organisation.created_by)
    api_client.force_authenticate(organisation.created_by)

    response = api_client.post(
        reverse("billing:change-plan", kwargs={"organisation_id": organisation.id}),
        {"plan_key": "professional"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["plan"]["key"] == "professional"


@pytest.mark.django_db
def test_change_plan_via_api_rejects_unknown_fields(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    create_subscription_for_organisation(organisation=organisation, actor=organisation.created_by)
    api_client.force_authenticate(organisation.created_by)

    response = api_client.post(
        reverse("billing:change-plan", kwargs={"organisation_id": organisation.id}),
        {"plan_key": "professional", "unexpected": "nope"},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_set_billing_contact_via_api(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    create_subscription_for_organisation(organisation=organisation, actor=organisation.created_by)
    api_client.force_authenticate(organisation.created_by)

    response = api_client.post(
        reverse("billing:set-billing-contact", kwargs={"organisation_id": organisation.id}),
        {"user_id": str(organisation.created_by.id)},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["billing_contact"]["id"] == str(organisation.created_by.id)

    subscription = OrganisationSubscription.objects.get(organisation=organisation)
    assert subscription.billing_contact_id == organisation.created_by.id
