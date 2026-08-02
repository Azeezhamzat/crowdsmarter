import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.organisations.models import Membership
from apps.workspaces.permissions import CanAccessWorkspace


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "can_patch"),
    [("owner", True), ("admin", True), ("contributor", False), ("viewer", False)],
)
def test_workspace_object_permission_matrix(
    user_factory, workspace_factory, role, can_patch
):  # type: ignore[no-untyped-def]
    workspace = workspace_factory()
    actor = workspace.organisation.created_by if role == "owner" else user_factory()
    if role != "owner":
        Membership.objects.create(organisation=workspace.organisation, user=actor, role=role)
    request = APIRequestFactory().patch("/", {})
    force_authenticate(request, actor)

    assert CanAccessWorkspace().has_object_permission(request, object(), workspace) is can_patch
