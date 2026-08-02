"""Object-level permissions for organisation invitations."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.organisations.models import Membership, Organisation

from .models import OrganisationInvitation


class CanManageInvitations(BasePermission):
    """Allow only active organisation owners and administrators."""

    def has_object_permission(
        self,
        request: Request,
        view: object,
        obj: Organisation | OrganisationInvitation,
    ) -> bool:
        organisation = obj.organisation if isinstance(obj, OrganisationInvitation) else obj
        membership = organisation.memberships.filter(
            user=request.user,
            status=Membership.Status.ACTIVE,
        ).first()
        return membership is not None and membership.role in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        }
