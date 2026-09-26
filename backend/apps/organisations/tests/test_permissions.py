import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.organisations.models import Membership
from apps.organisations.permissions import (
    CanManageMembership,
    CanManageOrganisation,
    IsOrganisationMember,
)


@pytest.mark.django_db
def test_is_organisation_member_denies_outsider(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    outsider = user_factory()
    organisation = organisation_factory()
    request = APIRequestFactory().get("/")
    force_authenticate(request, outsider)
    request = Request(request)

    assert not IsOrganisationMember().has_object_permission(request, object(), organisation)


@pytest.mark.django_db
def test_can_manage_organisation_allows_member_read_but_not_write(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    viewer = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
    )
    factory = APIRequestFactory()

    get_request = factory.get("/")
    force_authenticate(get_request, viewer)
    get_request = Request(get_request)
    patch_request = factory.patch("/", {})
    force_authenticate(patch_request, viewer)
    patch_request = Request(patch_request)

    permission = CanManageOrganisation()
    assert permission.has_object_permission(get_request, object(), organisation)
    assert not permission.has_object_permission(patch_request, object(), organisation)


@pytest.mark.django_db
def test_can_manage_membership_prevents_admin_changing_owner(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    owner = user_factory()
    admin = user_factory()
    organisation = organisation_factory(owner=owner)
    owner_membership = Membership.objects.get(organisation=organisation, user=owner)
    Membership.objects.create(
        organisation=organisation,
        user=admin,
        role=Membership.Role.ADMIN,
    )
    request = APIRequestFactory().patch("/", {})
    force_authenticate(request, admin)
    request = Request(request)

    assert not CanManageMembership().has_object_permission(request, object(), owner_membership)
