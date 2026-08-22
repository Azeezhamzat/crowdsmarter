"""REST representations for organisation lookup configuration and applicant verification."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import StrictSerializer

from .models import OrganisationLookupConfiguration


class LookupConfigurationSerializer(serializers.ModelSerializer):
    provider_key_label = serializers.CharField(source="get_provider_key_display", read_only=True)
    api_key_is_set = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrganisationLookupConfiguration
        fields = ["id", "organisation_id", "provider_key", "provider_key_label", "api_key_is_set", "created_at", "updated_at"]
        read_only_fields = fields


class SetLookupProviderSerializer(StrictSerializer):
    provider_key = serializers.ChoiceField(choices=OrganisationLookupConfiguration.ProviderKey.choices)


class SetLookupApiKeySerializer(StrictSerializer):
    api_key = serializers.CharField(max_length=4000)


class LookupOrganisationQuerySerializer(StrictSerializer):
    query = serializers.CharField(max_length=200)


class OrganisationLookupResultSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    found = serializers.BooleanField()
    legal_name = serializers.CharField()
    ein_or_charity_number = serializers.CharField()
    financial_summary = serializers.CharField()
    standing = serializers.CharField()
    detail = serializers.CharField()
