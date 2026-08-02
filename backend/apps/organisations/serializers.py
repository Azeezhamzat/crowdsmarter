"""API-only validation and representation for organisations."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.core.serializers import StrictSerializer

from .models import Membership, Organisation


class OrganisationSerializer(serializers.ModelSerializer):
    """Read representation of an organisation."""

    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = ["id", "name", "slug", "current_user_role", "created_at", "updated_at"]
        read_only_fields = fields

    def get_current_user_role(self, obj: Organisation) -> str | None:
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return None
        membership = next(
            (
                item
                for item in getattr(obj, "prefetched_active_memberships", [])
                if item.user_id == request.user.id
            ),
            None,
        )
        if membership is None:
            membership = obj.memberships.filter(
                user=request.user, status=Membership.Status.ACTIVE
            ).first()
        return membership.role if membership else None


class OrganisationCreateSerializer(StrictSerializer):
    """Input contract for tenant creation."""

    name = serializers.CharField(max_length=200, trim_whitespace=True)
    slug = serializers.SlugField(max_length=80)


class OrganisationUpdateSerializer(StrictSerializer):
    """Mutable organisation fields."""

    name = serializers.CharField(max_length=200, trim_whitespace=True)


class MembershipUserSerializer(serializers.ModelSerializer):
    """Minimal user identity shown within an organisation."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    """Read representation of an organisation membership."""

    organisation_id = serializers.UUIDField(read_only=True)
    user = MembershipUserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organisation_id", "user", "role", "status", "created_at", "updated_at"]
        read_only_fields = fields


class MembershipUpdateSerializer(StrictSerializer):
    """Input contract for role changes."""

    role = serializers.ChoiceField(choices=Membership.Role.choices)
