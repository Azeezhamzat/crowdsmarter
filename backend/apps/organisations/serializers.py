"""API-only validation and representation for organisations."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.core.serializers import StrictSerializer

from .models import Membership, MembershipEvent, Organisation, OrganisationDeletionRequest


class OrganisationSerializer(serializers.ModelSerializer):
    """Read representation of an organisation."""

    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = [
            "id", "name", "slug", "description", "website_url", "brand_name", "primary_colour",
            "invitation_policy", "default_invitation_role", "retention_days", "status",
            "deactivated_at", "current_user_role", "created_at", "updated_at",
        ]
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


class OrganisationAdministrationUpdateSerializer(StrictSerializer):
    """Mutable organisation profile, branding, invitation, and retention fields."""

    name = serializers.CharField(max_length=200, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=8000, trim_whitespace=True, allow_blank=True, required=False)
    website_url = serializers.URLField(max_length=500, allow_blank=True, required=False)
    brand_name = serializers.CharField(max_length=120, trim_whitespace=True, allow_blank=True, required=False)
    primary_colour = serializers.RegexField(r"^#[0-9A-Fa-f]{6}$", required=False)
    invitation_policy = serializers.ChoiceField(choices=Organisation.InvitationPolicy.choices, required=False)
    default_invitation_role = serializers.ChoiceField(
        choices=[Membership.Role.ADMIN, Membership.Role.CONTRIBUTOR, Membership.Role.VIEWER], required=False
    )
    retention_days = serializers.IntegerField(min_value=30, max_value=3650, allow_null=True, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one setting to update.")
        return attrs


class OwnershipTransferSerializer(StrictSerializer):
    target_membership_id = serializers.UUIDField()
    rationale = serializers.CharField(max_length=4000, trim_whitespace=True)


class OrganisationStateChangeSerializer(StrictSerializer):
    confirmation = serializers.CharField(max_length=300, trim_whitespace=True, required=False, default="")
    reason = serializers.CharField(max_length=4000, trim_whitespace=True, required=False, default="")
    rationale = serializers.CharField(max_length=4000, trim_whitespace=True, required=False, default="")


class MembershipEventSerializer(serializers.ModelSerializer):
    user = MembershipUserSerializer(read_only=True)
    actor = MembershipUserSerializer(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = MembershipEvent
        fields = [
            "id", "organisation_id", "membership_id_snapshot", "user", "actor", "kind", "kind_label",
            "previous_role", "new_role", "previous_status", "new_status", "note", "created_at",
        ]
        read_only_fields = fields


class OrganisationDeletionRequestSerializer(serializers.ModelSerializer):
    requested_by = MembershipUserSerializer(read_only=True)
    cancelled_by = MembershipUserSerializer(read_only=True)

    class Meta:
        model = OrganisationDeletionRequest
        fields = [
            "id", "organisation_id", "requested_by", "status", "reason", "earliest_deletion_at",
            "cancelled_by", "cancelled_at", "created_at", "updated_at",
        ]
        read_only_fields = fields
