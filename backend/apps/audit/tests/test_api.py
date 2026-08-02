import pytest
from django.urls import reverse

from apps.audit.services import record_event
from apps.organisations.models import Membership


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        (Membership.Role.OWNER, 200),
        (Membership.Role.ADMIN, 200),
        (Membership.Role.CONTRIBUTOR, 403),
        (Membership.Role.VIEWER, 403),
    ],
)
def test_audit_endpoint_permission_matrix(
    api_client,
    user_factory,
    organisation_factory,
    role,
    expected_status,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    actor = owner if role == Membership.Role.OWNER else user_factory()
    if actor != owner:
        Membership.objects.create(
            organisation=organisation,
            user=actor,
            role=role,
        )
    record_event(
        action="test.recorded",
        object_type="test",
        object_id="one",
        actor=owner,
        organisation=organisation,
    )
    api_client.force_authenticate(actor)

    response = api_client.get(
        reverse("audit:organisation-events", kwargs={"organisation_id": organisation.id})
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()[0]["action"] == "test.recorded"


@pytest.mark.django_db
def test_audit_endpoint_is_tenant_isolated(
    api_client,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    api_client.force_authenticate(user_factory())

    response = api_client.get(
        reverse("audit:organisation-events", kwargs={"organisation_id": organisation.id})
    )

    assert response.status_code == 404
