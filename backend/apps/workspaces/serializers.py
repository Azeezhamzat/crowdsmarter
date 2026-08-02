"""API contracts for workspace reads and writes."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.organisations.models import Membership

from .models import Workspace
from .policies import can_manage_workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    """Read representation with server-derived capabilities."""

    can_manage = serializers.SerializerMethodField()
    can_create_decisions = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = [
            "id",
            "organisation_id",
            "name",
            "slug",
            "description",
            "is_default",
            "can_manage",
            "can_create_decisions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_manage(self, obj: Workspace) -> bool:
        request = self.context.get("request")
        return bool(request and can_manage_workspace(actor=request.user, workspace=obj))

    def get_can_create_decisions(self, obj: Workspace) -> bool:
        request = self.context.get("request")
        if not request:
            return False
        return obj.organisation.memberships.filter(
            user=request.user,
            status=Membership.Status.ACTIVE,
            role__in=[
                Membership.Role.OWNER,
                Membership.Role.ADMIN,
                Membership.Role.CONTRIBUTOR,
            ],
        ).exists()


class WorkspaceCreateSerializer(StrictSerializer):
    """Input contract for creating an additional workspace."""

    name = serializers.CharField(max_length=160, trim_whitespace=True)
    slug = serializers.SlugField(max_length=80)
    description = serializers.CharField(max_length=2000, allow_blank=True, required=False)


class WorkspaceUpdateSerializer(StrictSerializer):
    """Mutable workspace fields."""

    name = serializers.CharField(max_length=160, trim_whitespace=True)
    description = serializers.CharField(max_length=2000, allow_blank=True)
