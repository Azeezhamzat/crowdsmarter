"""Shared pytest fixtures."""

from collections.abc import Callable

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organisations.models import Membership, Organisation

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user_factory(db) -> Callable[..., User]:  # type: ignore[no-untyped-def]
    counter = 0

    def create_user(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal counter
        counter += 1
        defaults = {
            "email": f"user{counter}@example.com",
            "password": "A-strong-test-password-123",
        }
        defaults.update(kwargs)
        password = defaults.pop("password")
        return User.objects.create_user(password=password, **defaults)

    return create_user


@pytest.fixture
def organisation_factory(
    db, user_factory
) -> Callable[..., Organisation]:  # type: ignore[no-untyped-def]
    counter = 0

    def create_organisation(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal counter
        counter += 1
        owner = kwargs.pop("owner", user_factory())
        organisation = Organisation.objects.create(
            name=kwargs.pop("name", f"Organisation {counter}"),
            slug=kwargs.pop("slug", f"organisation-{counter}"),
            created_by=owner,
            **kwargs,
        )
        Membership.objects.create(
            organisation=organisation,
            user=owner,
            role=Membership.Role.OWNER,
            status=Membership.Status.ACTIVE,
        )
        from apps.workspaces.models import Workspace

        Workspace.objects.create(
            organisation=organisation,
            name="Decisions",
            slug="decisions",
            description="The organisation's primary decision workspace.",
            is_default=True,
            created_by=owner,
        )
        return organisation

    return create_organisation


@pytest.fixture
def workspace_factory(db, organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    """Create tenant-owned workspaces without invoking service permissions."""
    from apps.workspaces.models import Workspace

    counter = 0

    def create_workspace(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal counter
        counter += 1
        organisation = kwargs.pop("organisation", organisation_factory())
        created_by = kwargs.pop("created_by", organisation.created_by)
        return Workspace.objects.create(
            organisation=organisation,
            name=kwargs.pop("name", f"Workspace {counter}"),
            slug=kwargs.pop("slug", f"workspace-{counter}"),
            description=kwargs.pop("description", ""),
            created_by=created_by,
            **kwargs,
        )

    return create_workspace


@pytest.fixture
def decision_factory(db, workspace_factory, user_factory):  # type: ignore[no-untyped-def]
    """Create a decision plus its system-managed owner participant."""
    from apps.decisions.models import Decision
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    counter = 0

    def create_decision(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal counter
        counter += 1
        workspace = kwargs.pop("workspace", workspace_factory())
        owner = kwargs.pop("owner", workspace.organisation.created_by)
        Membership.objects.get_or_create(
            organisation=workspace.organisation,
            user=owner,
            defaults={"role": Membership.Role.CONTRIBUTOR, "status": Membership.Status.ACTIVE},
        )
        decision = Decision.objects.create(
            organisation=workspace.organisation,
            workspace=workspace,
            title=kwargs.pop("title", f"Decision {counter}"),
            owner=owner,
            created_by=kwargs.pop("created_by", owner),
            **kwargs,
        )
        Participant.objects.create(
            organisation=workspace.organisation,
            decision=decision,
            user=owner,
            role=Participant.Role.DECISION_OWNER,
            added_by=decision.created_by,
        )
        return decision

    return create_decision
