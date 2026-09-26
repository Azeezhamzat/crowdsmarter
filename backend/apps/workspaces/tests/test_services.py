import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.organisations.models import Membership
from apps.workspaces.models import Workspace
from apps.workspaces.services import create_workspace, update_workspace


@pytest.mark.django_db
def test_manager_creates_workspace_and_audit(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)

    workspace = create_workspace(
        actor=owner,
        organisation=organisation,
        name="  Strategy  ",
        slug="STRATEGY",
        description="  Strategic decisions.  ",
    )

    assert workspace.name == "Strategy"
    assert workspace.slug == "strategy"
    assert workspace.description == "Strategic decisions."
    assert AuditEvent.objects.filter(
        action="workspace.created",
        object_id=str(workspace.id),
    ).exists()


@pytest.mark.django_db
def test_contributor_cannot_create_workspace(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )

    with pytest.raises(PermissionDenied):
        create_workspace(
            actor=contributor,
            organisation=organisation,
            name="Not allowed",
            slug="not-allowed",
        )


@pytest.mark.django_db
def test_manager_updates_workspace(workspace_factory):  # type: ignore[no-untyped-def]
    workspace = workspace_factory()
    owner = workspace.organisation.created_by

    updated = update_workspace(
        actor=owner,
        workspace=workspace,
        name="Executive decisions",
        description="Material cross-functional decisions.",
    )

    assert updated.name == "Executive decisions"
    assert (
        Workspace.objects.get(id=workspace.id).description == "Material cross-functional decisions."
    )
