"""Named workspace capabilities derived from organisation membership."""

from __future__ import annotations

from apps.accounts.models import User
from apps.organisations.models import Membership

from .models import Workspace


def active_membership(*, actor: User, workspace: Workspace) -> Membership | None:
    """Return the actor's active membership for a workspace tenant."""
    return workspace.organisation.memberships.filter(
        user=actor,
        status=Membership.Status.ACTIVE,
    ).first()


def can_manage_workspace(*, actor: User, workspace: Workspace) -> bool:
    """Return whether the actor may change workspace configuration."""
    membership = active_membership(actor=actor, workspace=workspace)
    return membership is not None and membership.role in {
        Membership.Role.OWNER,
        Membership.Role.ADMIN,
    }
