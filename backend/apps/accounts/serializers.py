"""API serializers for authentication."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.serializers import StrictSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Safe public representation of the current user."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = fields


class LoginSerializer(StrictSerializer):
    """Credentials accepted by the session login endpoint."""

    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)
