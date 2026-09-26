"""Object-level organisation permissions.

Service methods repeat material authorisation checks so permissions remain safe
when workflows are called from admin commands, tasks, or future interfaces.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from .models import Membership, Organisation


class IsOrganisationMember(BasePermission):
    """Allow active tenant members to read an organisation."""

    def has_object_permission(
        self,
        request: Request,
        view: object,
        obj: Organisation,
    ) -> bool:
        user_id = request.user.pk
        if user_id is None:
            return False
        return obj.memberships.filter(
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).exists()


class CanManageOrganisation(BasePermission):
    """Allow reads to members and writes to owners or administrators."""

    def has_object_permission(
        self,
        request: Request,
        view: object,
        obj: Organisation,
    ) -> bool:
        user_id = request.user.pk
        if user_id is None:
            return False
        membership = obj.memberships.filter(
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).first()
        if membership is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}


class CanManageMembership(BasePermission):
    """Apply membership administration rules before entering services."""

    def has_object_permission(
        self,
        request: Request,
        view: object,
        obj: Membership,
    ) -> bool:
        user_id = request.user.pk
        if user_id is None:
            return False
        actor_membership = obj.organisation.memberships.filter(
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).first()
        if actor_membership is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        if actor_membership.role == Membership.Role.OWNER:
            return True
        return actor_membership.role == Membership.Role.ADMIN and obj.role != Membership.Role.OWNER
