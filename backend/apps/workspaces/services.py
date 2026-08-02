"""Transactional workspace workflows."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.organisations.models import Membership, Organisation

from .models import Workspace


class WorkspaceServiceError(ValidationError):
    """Expected validation failure in a workspace workflow."""


def _require_manager(*, actor: User, organisation: Organisation) -> Membership:
    try:
        membership = Membership.objects.get(
            organisation=organisation,
            user=actor,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("You are not an active member of this organisation.") from exc
    if membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        raise PermissionDenied("This action requires an owner or administrator role.")
    return membership


@transaction.atomic
def create_default_workspace(*, organisation: Organisation, actor: User) -> Workspace:
    """Create the single low-friction default workspace for a new tenant."""
    workspace, created = Workspace.objects.get_or_create(
        organisation=organisation,
        is_default=True,
        defaults={
            "name": "Decisions",
            "slug": "decisions",
            "description": "The organisation's primary decision workspace.",
            "created_by": actor,
        },
    )
    if created:
        record_event(
            action="workspace.created",
            object_type="workspace",
            object_id=str(workspace.id),
            actor=actor,
            organisation=organisation,
            metadata={"name": workspace.name, "slug": workspace.slug, "is_default": True},
        )
    return workspace


@transaction.atomic
def create_workspace(
    *,
    actor: User,
    organisation: Organisation,
    name: str,
    slug: str,
    description: str = "",
) -> Workspace:
    """Create a workspace under tenant management rules."""
    _require_manager(actor=actor, organisation=organisation)
    if organisation.status != Organisation.Status.ACTIVE:
        raise WorkspaceServiceError("Reactivate the organisation before creating a workspace.")
    workspace = Workspace(
        organisation=organisation,
        name=name,
        slug=slug,
        description=description,
        created_by=actor,
    )
    workspace.full_clean(validate_unique=False, validate_constraints=False)
    try:
        workspace.save()
    except IntegrityError as exc:
        raise WorkspaceServiceError(
            "That workspace URL identifier is already in use in this organisation."
        ) from exc
    record_event(
        action="workspace.created",
        object_type="workspace",
        object_id=str(workspace.id),
        actor=actor,
        organisation=organisation,
        metadata={"name": workspace.name, "slug": workspace.slug, "is_default": False},
    )
    return workspace


@transaction.atomic
def update_workspace(
    *,
    actor: User,
    workspace: Workspace,
    name: str,
    description: str,
) -> Workspace:
    """Update the human-facing workspace configuration."""
    workspace = Workspace.objects.select_for_update().select_related("organisation").get(
        id=workspace.id
    )
    _require_manager(actor=actor, organisation=workspace.organisation)
    previous = {"name": workspace.name, "description": workspace.description}
    workspace.name = name
    workspace.description = description
    workspace.full_clean(exclude=["created_by"], validate_unique=False)
    workspace.save(update_fields=["name", "description", "updated_at"])
    record_event(
        action="workspace.updated",
        object_type="workspace",
        object_id=str(workspace.id),
        actor=actor,
        organisation=workspace.organisation,
        metadata={
            "previous": previous,
            "name": workspace.name,
            "description": workspace.description,
        },
    )
    return workspace
