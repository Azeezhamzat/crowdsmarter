"""Public demo-request API contracts."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer

from .models import DemoRequest


class DemoRequestCreateSerializer(StrictSerializer):
    """Validated public fields accepted from the request-demo form."""

    full_name = serializers.CharField(max_length=160)
    work_email = serializers.EmailField(max_length=254)
    organisation_name = serializers.CharField(max_length=200)
    job_title = serializers.CharField(max_length=160, required=False, allow_blank=True)
    organisation_size = serializers.ChoiceField(choices=DemoRequest.OrganisationSize.choices)
    primary_need = serializers.ChoiceField(choices=DemoRequest.PrimaryNeed.choices)
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    consent_to_contact = serializers.BooleanField()
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate_full_name(self, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter your full name.")
        return value

    def validate_organisation_name(self, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter your organisation name.")
        return value

    def validate_consent_to_contact(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(
                "Consent is required so the CrowdSmarter team may respond to this request."
            )
        return value

    def validate_website(self, value: str) -> str:
        if value.strip():
            raise serializers.ValidationError("This request could not be accepted.")
        return ""
