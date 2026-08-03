"""API serializers for authentication and account self-service."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.serializers import StrictSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Safe public representation of the current user."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = fields


class CurrentUserSerializer(UserSerializer):
    """Current-user representation with safe administration capability metadata."""

    is_staff = serializers.BooleanField(read_only=True)
    is_platform_administrator = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, "is_staff", "is_platform_administrator"]
        read_only_fields = fields

    def get_is_platform_administrator(self, obj) -> bool:  # type: ignore[no-untyped-def]
        from apps.platform_admin.permissions import is_platform_administrator

        return is_platform_administrator(obj)


class LoginSerializer(StrictSerializer):
    """Credentials accepted by the session login endpoint."""

    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_email(self, value: str) -> str:
        """Normalise browser and password-manager variations consistently."""
        return value.strip().lower()


class ProfileUpdateSerializer(StrictSerializer):
    """Editable personal profile fields."""

    first_name = serializers.CharField(max_length=150, allow_blank=True)
    last_name = serializers.CharField(max_length=150, allow_blank=True)

    def validate_first_name(self, value: str) -> str:
        return value.strip()

    def validate_last_name(self, value: str) -> str:
        return value.strip()


class PasswordChangeSerializer(StrictSerializer):
    """Authenticated password-change command."""

    current_password = serializers.CharField(trim_whitespace=False, write_only=True)
    new_password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_new_password(self, value: str) -> str:
        validate_password(value, user=self.context.get("user"))
        return value


class PasswordResetRequestSerializer(StrictSerializer):
    """Anonymous password-reset request."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(StrictSerializer):
    """Anonymous password-reset confirmation."""

    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=256)
    new_password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_new_password(self, value: str) -> str:
        validate_password(value, user=self.context.get("user"))
        return value


class MFACodeSerializer(StrictSerializer):
    """A six-digit authenticator code or a formatted backup code."""

    code = serializers.CharField(max_length=32, trim_whitespace=True)


class MFADisableSerializer(StrictSerializer):
    """Require the current password before turning off two-factor authentication."""

    password = serializers.CharField(trim_whitespace=False, write_only=True)
