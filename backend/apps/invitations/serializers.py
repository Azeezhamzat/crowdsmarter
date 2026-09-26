"""API contracts for organisation invitations."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.core.serializers import StrictSerializer
from apps.organisations.models import Membership

from .models import OrganisationInvitation
from .services import effective_status

User = get_user_model()


class InvitationSerializer(serializers.ModelSerializer):
    """Manager-facing invitation representation."""

    organisation_id = serializers.UUIDField(read_only=True)
    status = serializers.SerializerMethodField()
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    invited_by = UserSerializer(read_only=True)
    accepted_by = UserSerializer(read_only=True)

    class Meta:
        model = OrganisationInvitation
        fields = [
            "id",
            "organisation_id",
            "email",
            "role",
            "role_label",
            "status",
            "invited_by",
            "accepted_by",
            "expires_at",
            "accepted_at",
            "revoked_at",
            "last_sent_at",
            "send_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_status(self, obj: OrganisationInvitation) -> str:
        return effective_status(obj)


class InvitationCreateSerializer(StrictSerializer):
    """Input contract for inviting one person."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Membership.Role.choices)


class InvitationPublicSerializer(serializers.ModelSerializer):
    """Minimal information disclosed to the holder of a valid secret link."""

    organisation_id = serializers.UUIDField(read_only=True)
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)
    status = serializers.SerializerMethodField()
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    account_exists = serializers.SerializerMethodField()

    class Meta:
        model = OrganisationInvitation
        fields = [
            "organisation_id",
            "organisation_name",
            "email",
            "role",
            "role_label",
            "status",
            "expires_at",
            "account_exists",
        ]
        read_only_fields = fields

    def get_status(self, obj: OrganisationInvitation) -> str:
        return effective_status(obj)

    def get_account_exists(self, obj: OrganisationInvitation) -> bool:
        return User.objects.filter(email__iexact=obj.email).exists()


class InvitationAcceptSerializer(StrictSerializer):
    """Account details used only when the invited email has no account."""

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        required=False,
        allow_blank=True,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        password = attrs.get("password", "")
        confirmation = attrs.pop("password_confirm", "")
        if (password or confirmation) and password != confirmation:
            raise serializers.ValidationError({"password_confirm": ["The passwords do not match."]})
        return attrs
