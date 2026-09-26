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
        user_id = request.user.pk
        if user_id is None:
            return False
        membership = organisation.memberships.filter(
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).first()
        if membership is None or organisation.status != Organisation.Status.ACTIVE:
            return False
        if organisation.invitation_policy == Organisation.InvitationPolicy.OWNERS_ONLY:
            return membership.role == Membership.Role.OWNER
        return membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}
