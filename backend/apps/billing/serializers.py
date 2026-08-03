"""Strict API contracts for plan entitlements and subscriptions."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import OrganisationSubscription, Plan


class PlanSerializer(serializers.ModelSerializer):
    support_level_label = serializers.CharField(source="get_support_level_display", read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "key",
            "name",
            "description",
            "trial_days",
            "max_active_decisions",
            "max_active_members",
            "includes_advanced_foresight",
            "includes_ai_assistance",
            "support_level",
            "support_level_label",
        ]
        read_only_fields = fields


class OrganisationSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    billing_contact = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_trial_expired = serializers.BooleanField(read_only=True)
    active_decision_count = serializers.SerializerMethodField()
    active_member_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganisationSubscription
        fields = [
            "id",
            "organisation_id",
            "plan",
            "status",
            "status_label",
            "trial_ends_at",
            "is_trial_expired",
            "billing_contact",
            "started_at",
            "active_decision_count",
            "active_member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_active_decision_count(self, obj: OrganisationSubscription) -> int:
        from apps.decisions.models import Decision

        return Decision.objects.filter(organisation=obj.organisation_id).exclude(
            status=Decision.Status.ARCHIVED
        ).count()

    def get_active_member_count(self, obj: OrganisationSubscription) -> int:
        from apps.organisations.models import Membership

        return Membership.objects.filter(
            organisation=obj.organisation_id, status=Membership.Status.ACTIVE
        ).count()


class ChangePlanSerializer(StrictSerializer):
    plan_key = serializers.SlugField(max_length=40)


class SetBillingContactSerializer(StrictSerializer):
    user_id = serializers.UUIDField(required=False, allow_null=True)
