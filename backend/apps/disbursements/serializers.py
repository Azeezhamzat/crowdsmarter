"""REST representations for organisation disbursement configuration and the payout ledger."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import Disbursement, OrganisationDisbursementConfiguration


class DisbursementConfigurationSerializer(serializers.ModelSerializer):
    provider_key_label = serializers.CharField(source="get_provider_key_display", read_only=True)
    api_key_is_set = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrganisationDisbursementConfiguration
        fields = ["id", "organisation_id", "provider_key", "provider_key_label", "stripe_account_id", "api_key_is_set", "created_at", "updated_at"]
        read_only_fields = fields


class SetDisbursementProviderSerializer(StrictSerializer):
    provider_key = serializers.ChoiceField(choices=OrganisationDisbursementConfiguration.ProviderKey.choices)
    stripe_account_id = serializers.CharField(required=False, allow_blank=True, max_length=100, default="")


class SetDisbursementApiKeySerializer(StrictSerializer):
    api_key = serializers.CharField(max_length=4000)


class DisbursementSerializer(serializers.ModelSerializer):
    provider_key_label = serializers.CharField(source="get_provider_key_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    issued_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = Disbursement
        fields = ["id", "option_id", "amount", "provider_key", "provider_key_label", "status", "status_label", "external_reference", "note", "issued_by", "created_at"]
        read_only_fields = fields


class IssueDisbursementSerializer(StrictSerializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    note = serializers.CharField(required=False, allow_blank=True, max_length=4000, default="")
