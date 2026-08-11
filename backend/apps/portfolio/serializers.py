"""Read-only API representations for portfolio views."""

from rest_framework import serializers

from apps.decisions.models import Decision
from apps.decisions.serializers import DecisionUserSerializer
from apps.organisations.serializers import OrganisationSerializer


class PortfolioWorkspaceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class PortfolioDecisionSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)
    workspace = PortfolioWorkspaceSerializer(read_only=True)
    owner = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    participant_role = serializers.CharField(read_only=True, allow_null=True)
    unresolved_discussion_count = serializers.IntegerField(read_only=True)
    next_action = serializers.CharField(source="portfolio_next_action", read_only=True)
    due_date = serializers.DateField(
        source="portfolio_due_date",
        read_only=True,
        allow_null=True,
    )
    is_overdue = serializers.BooleanField(
        source="portfolio_is_overdue",
        read_only=True,
    )

    class Meta:
        model = Decision
        fields = [
            "id",
            "organisation_id",
            "organisation_name",
            "workspace",
            "title",
            "decision_question",
            "status",
            "status_label",
            "urgency",
            "target_decision_date",
            "owner",
            "participant_role",
            "unresolved_discussion_count",
            "next_action",
            "due_date",
            "is_overdue",
            "updated_at",
        ]
        read_only_fields = fields


class PortfolioSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    overdue = serializers.IntegerField()
    unresolved_discussion = serializers.IntegerField()
    status_counts = serializers.DictField(child=serializers.IntegerField())


class WatchlistStalledDecisionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    status = serializers.CharField()
    status_label = serializers.CharField()
    days_stalled = serializers.IntegerField()


class WatchlistRiskSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    decision_id = serializers.UUIDField()
    decision_title = serializers.CharField()
    likelihood = serializers.IntegerField()
    impact = serializers.IntegerField()


class WatchlistAssumptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    statement = serializers.CharField()
    decision_id = serializers.UUIDField()
    decision_title = serializers.CharField()
    verification_status = serializers.CharField()
    verification_status_label = serializers.CharField()


class WatchlistSignpostObservationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    signpost_id = serializers.UUIDField()
    signpost_title = serializers.CharField()
    scenario_set_id = serializers.UUIDField()
    canvas_id = serializers.UUIDField()
    assessment = serializers.CharField()
    assessment_label = serializers.CharField()
    observed_on = serializers.DateField()


class BenefitsRealizationSerializer(serializers.Serializer):
    exceeded = serializers.IntegerField()
    met = serializers.IntegerField()
    partially_met = serializers.IntegerField()
    not_met = serializers.IntegerField()
    inconclusive = serializers.IntegerField()
    total_reviewed = serializers.IntegerField()


class RiskHeatmapRiskSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    decision_id = serializers.UUIDField()
    decision_title = serializers.CharField()


class RiskHeatmapCellSerializer(serializers.Serializer):
    likelihood = serializers.IntegerField()
    impact = serializers.IntegerField()
    count = serializers.IntegerField()
    risks = RiskHeatmapRiskSerializer(many=True)


class RiskHeatmapSerializer(serializers.Serializer):
    cells = RiskHeatmapCellSerializer(many=True)
    total_open_risks = serializers.IntegerField()


class PortfolioWatchlistSerializer(serializers.Serializer):
    stalled_decisions = WatchlistStalledDecisionSerializer(many=True)
    open_high_risks = WatchlistRiskSerializer(many=True)
    assumptions_at_risk = WatchlistAssumptionSerializer(many=True)
    triggered_signposts = WatchlistSignpostObservationSerializer(many=True)
    benefits_realization = BenefitsRealizationSerializer()
    risk_heatmap = RiskHeatmapSerializer()


class OrganisationPortfolioSerializer(serializers.Serializer):
    organisation = OrganisationSerializer()
    summary = PortfolioSummarySerializer()
    decisions = PortfolioDecisionSerializer(many=True)
    watchlist = PortfolioWatchlistSerializer()


class PersonalWorkSerializer(serializers.Serializer):
    unread_notifications = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    decision_count = serializers.IntegerField()
    decisions = PortfolioDecisionSerializer(many=True)
