"""API contracts for platform administration."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.audit.serializers import AuditEventSerializer
from apps.core.serializers import StrictSerializer
from apps.demo_requests.models import DemoRequest
from apps.invitations.models import OrganisationInvitation
from apps.organisations.models import Membership, Organisation

from .models import PlatformAdministrator, PlatformConfiguration, SupportAccessGrant
from .permissions import is_platform_administrator

User = get_user_model()


class PlatformAdministratorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    granted_by = UserSerializer(read_only=True)
    suspended_by = UserSerializer(read_only=True)

    class Meta:
        model = PlatformAdministrator
        fields = [
            "id",
            "user",
            "status",
            "rationale",
            "granted_by",
            "suspended_by",
            "suspended_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PlatformUserSerializer(serializers.ModelSerializer):
    is_platform_administrator = serializers.SerializerMethodField()
    organisation_count = serializers.IntegerField(read_only=True)
    active_owned_organisation_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_platform_administrator",
            "organisation_count",
            "active_owned_organisation_count",
            "date_joined",
            "last_login",
        ]
        read_only_fields = fields

    def get_is_platform_administrator(self, obj) -> bool:  # type: ignore[no-untyped-def]
        return is_platform_administrator(obj)


class PlatformUserStateSerializer(StrictSerializer):
    is_active = serializers.BooleanField()
    rationale = serializers.CharField(min_length=12, max_length=1000)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


class PlatformAdministratorGrantSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=[("grant", "Grant"), ("suspend", "Suspend")])
    rationale = serializers.CharField(min_length=12, max_length=1000)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


class PlatformOrganisationSummarySerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    active_owner_count = serializers.IntegerField(read_only=True)
    workspace_count = serializers.IntegerField(read_only=True)
    decision_count = serializers.IntegerField(read_only=True)
    active_decision_count = serializers.IntegerField(read_only=True)
    pending_invitation_count = serializers.IntegerField(read_only=True)
    owners = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "brand_name",
            "website_url",
            "primary_colour",
            "status",
            "retention_days",
            "created_at",
            "updated_at",
            "member_count",
            "active_owner_count",
            "workspace_count",
            "decision_count",
            "active_decision_count",
            "pending_invitation_count",
            "owners",
        ]
        read_only_fields = fields

    def get_owners(self, obj) -> list[dict[str, str]]:  # type: ignore[no-untyped-def]
        owners = getattr(obj, "prefetched_platform_owners", None)
        if owners is None:
            owners = obj.memberships.filter(
                role=Membership.Role.OWNER,
                status=Membership.Status.ACTIVE,
            ).select_related("user")
        return [
            {
                "membership_id": str(membership.id),
                "user_id": str(membership.user_id),
                "email": membership.user.email,
                "name": (
                    f"{membership.user.first_name} {membership.user.last_name}".strip()
                    or membership.user.email
                ),
            }
            for membership in owners
        ]


class PlatformMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "role", "status", "created_at", "updated_at"]
        read_only_fields = fields


class PlatformInvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)
    effective_status = serializers.SerializerMethodField()

    class Meta:
        model = OrganisationInvitation
        fields = [
            "id",
            "email",
            "role",
            "status",
            "effective_status",
            "invited_by",
            "expires_at",
            "last_sent_at",
            "send_count",
            "created_at",
        ]
        read_only_fields = fields

    def get_effective_status(self, obj) -> str:  # type: ignore[no-untyped-def]
        from apps.invitations.services import effective_status

        return effective_status(obj)


class PlatformOrganisationDetailSerializer(PlatformOrganisationSummarySerializer):
    memberships = PlatformMembershipSerializer(many=True, read_only=True)
    invitations = PlatformInvitationSerializer(many=True, read_only=True)
    workspaces = serializers.SerializerMethodField()
    decisions = serializers.SerializerMethodField()
    current_support_access = serializers.SerializerMethodField()

    class Meta(PlatformOrganisationSummarySerializer.Meta):
        fields = [
            *PlatformOrganisationSummarySerializer.Meta.fields,
            "memberships",
            "invitations",
            "workspaces",
            "decisions",
            "current_support_access",
        ]

    def get_workspaces(self, obj) -> list[dict[str, object]]:  # type: ignore[no-untyped-def]
        return [
            {
                "id": str(item.id),
                "name": item.name,
                "slug": item.slug,
                "is_default": item.is_default,
                "decision_count": getattr(item, "platform_decision_count", item.decisions.count()),
            }
            for item in obj.workspaces.all()[:100]
        ]

    def get_decisions(self, obj) -> list[dict[str, object]]:  # type: ignore[no-untyped-def]
        return [
            {
                "id": str(item.id),
                "title": item.title,
                "status": item.status,
                "urgency": item.urgency,
                "owner": {
                    "id": str(item.owner_id),
                    "email": item.owner.email,
                    "name": f"{item.owner.first_name} {item.owner.last_name}".strip() or item.owner.email,
                },
                "updated_at": item.updated_at,
            }
            for item in obj.decisions.select_related("owner").all()[:100]
        ]

    def get_current_support_access(self, obj):  # type: ignore[no-untyped-def]
        request = self.context.get("request")
        if request is None:
            return None
        grant = getattr(obj, "current_platform_support_grant", None)
        if grant is None:
            return None
        return SupportAccessGrantSerializer(grant).data


class SupportAccessGrantSerializer(serializers.ModelSerializer):
    administrator = UserSerializer(read_only=True)
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)
    revoked_by = UserSerializer(read_only=True)
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = SupportAccessGrant
        fields = [
            "id",
            "administrator",
            "organisation",
            "organisation_name",
            "access_level",
            "reason",
            "status",
            "expires_at",
            "revoked_by",
            "revoked_at",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SupportAccessCreateSerializer(StrictSerializer):
    access_level = serializers.ChoiceField(choices=SupportAccessGrant.AccessLevel.choices)
    reason = serializers.CharField(min_length=12, max_length=2000)
    duration_hours = serializers.IntegerField(min_value=1, max_value=72)

    def validate_reason(self, value: str) -> str:
        return value.strip()


class PlatformOwnershipTransferSerializer(StrictSerializer):
    target_membership_id = serializers.UUIDField()
    rationale = serializers.CharField(min_length=12, max_length=2000)
    demote_existing_owners = serializers.BooleanField(default=True)
    confirmation = serializers.CharField(max_length=240)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


class PlatformOrganisationStateSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=[("deactivate", "Deactivate"), ("reactivate", "Reactivate")])
    rationale = serializers.CharField(min_length=12, max_length=2000)
    confirmation = serializers.CharField(max_length=240)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


class PlatformInvitationActionSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=[("resend", "Resend"), ("revoke", "Revoke")])
    rationale = serializers.CharField(min_length=12, max_length=1000)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


class PlatformConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformConfiguration
        fields = [
            "public_contact_email",
            "demo_email",
            "support_email",
            "privacy_email",
            "security_email",
            "notification_sender_email",
            "support_access_max_hours",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class PlatformConfigurationUpdateSerializer(StrictSerializer):
    public_contact_email = serializers.EmailField()
    demo_email = serializers.EmailField()
    support_email = serializers.EmailField()
    privacy_email = serializers.EmailField()
    security_email = serializers.EmailField()
    notification_sender_email = serializers.EmailField()
    support_access_max_hours = serializers.IntegerField(min_value=1, max_value=72)
    rationale = serializers.CharField(min_length=12, max_length=1000)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


class PlatformDemoRequestSerializer(serializers.ModelSerializer):
    primary_need_label = serializers.CharField(source="get_primary_need_display", read_only=True)
    organisation_size_label = serializers.CharField(source="get_organisation_size_display", read_only=True)

    class Meta:
        model = DemoRequest
        fields = [
            "id",
            "full_name",
            "work_email",
            "organisation_name",
            "job_title",
            "organisation_size",
            "organisation_size_label",
            "primary_need",
            "primary_need_label",
            "message",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PlatformDemoRequestStatusSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=DemoRequest.Status.choices)
    rationale = serializers.CharField(min_length=12, max_length=1000)

    def validate_rationale(self, value: str) -> str:
        return value.strip()


__all__ = [
    "AuditEventSerializer",
    "PlatformAdministratorSerializer",
    "PlatformConfigurationSerializer",
    "PlatformConfigurationUpdateSerializer",
    "PlatformDemoRequestSerializer",
    "PlatformDemoRequestStatusSerializer",
    "PlatformInvitationActionSerializer",
    "PlatformOrganisationDetailSerializer",
    "PlatformOrganisationStateSerializer",
    "PlatformOrganisationSummarySerializer",
    "PlatformOwnershipTransferSerializer",
    "PlatformUserSerializer",
    "PlatformUserStateSerializer",
    "PlatformAdministratorGrantSerializer",
    "SupportAccessCreateSerializer",
    "SupportAccessGrantSerializer",
]
