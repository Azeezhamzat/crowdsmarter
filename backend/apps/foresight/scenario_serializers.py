"""REST contracts for scenario planning, wind-tunnelling, and signposts."""

from statistics import mean

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import (
    Scenario,
    ScenarioDriverState,
    ScenarioImplicationLink,
    ScenarioReview,
    ScenarioSet,
    ScenarioSignpost,
    Signpost,
    SignpostObservation,
    WindTunnelAssessment,
)
from .policies import can_manage_record


class ScenarioSetSerializer(serializers.ModelSerializer):
    axis_x_driver_id = serializers.UUIDField(read_only=True)
    axis_x_driver_title = serializers.CharField(source="axis_x_driver.title", read_only=True)
    axis_y_driver_id = serializers.UUIDField(read_only=True)
    axis_y_driver_title = serializers.CharField(source="axis_y_driver.title", read_only=True)
    linked_decision_id = serializers.UUIDField(read_only=True, allow_null=True)
    linked_decision_title = serializers.CharField(
        source="linked_decision.title", read_only=True, allow_null=True
    )
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    scenario_count = serializers.SerializerMethodField()
    signpost_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ScenarioSet
        fields = [
            "id",
            "canvas_id",
            "title",
            "purpose",
            "axis_x_driver_id",
            "axis_x_driver_title",
            "axis_x_low_label",
            "axis_x_high_label",
            "axis_y_driver_id",
            "axis_y_driver_title",
            "axis_y_low_label",
            "axis_y_high_label",
            "linked_decision_id",
            "linked_decision_title",
            "owner",
            "created_by",
            "status",
            "status_label",
            "scenario_count",
            "signpost_count",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_scenario_count(self, obj: ScenarioSet) -> int:
        annotated = getattr(obj, "scenario_count", None)
        return int(annotated) if annotated is not None else obj.scenarios.count()

    def get_signpost_count(self, obj: ScenarioSet) -> int:
        annotated = getattr(obj, "signpost_count", None)
        return int(annotated) if annotated is not None else obj.signposts.count()

    def get_can_edit(self, obj: ScenarioSet) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.canvas.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
            and obj.canvas.status != "archived"
            and obj.status != ScenarioSet.Status.ARCHIVED
        )


class ScenarioSetWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    purpose = serializers.CharField(max_length=12000, trim_whitespace=True)
    axis_x_driver_id = serializers.UUIDField()
    axis_x_low_label = serializers.CharField(max_length=160, trim_whitespace=True)
    axis_x_high_label = serializers.CharField(max_length=160, trim_whitespace=True)
    axis_y_driver_id = serializers.UUIDField()
    axis_y_low_label = serializers.CharField(max_length=160, trim_whitespace=True)
    axis_y_high_label = serializers.CharField(max_length=160, trim_whitespace=True)
    linked_decision_id = serializers.UUIDField(required=False, allow_null=True)
    owner_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=ScenarioSet.Status.choices,
        required=False,
        default=ScenarioSet.Status.DRAFT,
    )


class ScenarioSetPatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    purpose = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    axis_x_low_label = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    axis_x_high_label = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    axis_y_low_label = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    axis_y_high_label = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    linked_decision_id = serializers.UUIDField(required=False, allow_null=True)
    owner_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=ScenarioSet.Status.choices, required=False)


class ScenarioDriverStateSerializer(serializers.ModelSerializer):
    driver_id = serializers.UUIDField(read_only=True)
    driver_title = serializers.CharField(source="driver.title", read_only=True)
    state_label = serializers.CharField(source="get_state_display", read_only=True)
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = ScenarioDriverState
        fields = [
            "id",
            "scenario_id",
            "driver_id",
            "driver_title",
            "state",
            "state_label",
            "salience",
            "description",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ScenarioReviewSerializer(serializers.ModelSerializer):
    reviewer = DecisionUserSerializer(read_only=True)

    class Meta:
        model = ScenarioReview
        fields = [
            "id",
            "scenario_id",
            "reviewer",
            "plausibility",
            "internal_consistency",
            "distinctiveness",
            "usefulness",
            "confidence",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class WindTunnelAssessmentSerializer(serializers.ModelSerializer):
    option_id = serializers.UUIDField(read_only=True)
    option_title = serializers.CharField(source="option.title", read_only=True)
    decision_id = serializers.UUIDField(source="option.decision_id", read_only=True)
    decision_title = serializers.CharField(source="option.decision.title", read_only=True)
    verdict_label = serializers.CharField(source="get_verdict_display", read_only=True)
    assessed_by = DecisionUserSerializer(read_only=True)
    robustness_score = serializers.FloatField(read_only=True)

    class Meta:
        model = WindTunnelAssessment
        fields = [
            "id",
            "scenario_id",
            "option_id",
            "option_title",
            "decision_id",
            "decision_title",
            "verdict",
            "verdict_label",
            "desirability",
            "feasibility",
            "resilience",
            "robustness_score",
            "rationale",
            "conditions_for_success",
            "vulnerabilities",
            "mitigations",
            "assessed_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ScenarioImplicationLinkSerializer(serializers.ModelSerializer):
    implication_id = serializers.UUIDField(read_only=True)
    implication_title = serializers.CharField(source="implication.title", read_only=True)
    implication_type = serializers.CharField(source="implication.implication_type", read_only=True)
    effect_label = serializers.CharField(source="get_effect_display", read_only=True)
    linked_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = ScenarioImplicationLink
        fields = [
            "id",
            "scenario_id",
            "implication_id",
            "implication_title",
            "implication_type",
            "effect",
            "effect_label",
            "rationale",
            "linked_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ScenarioSerializer(serializers.ModelSerializer):
    created_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    axis_x_position_label = serializers.CharField(
        source="get_axis_x_position_display", read_only=True
    )
    axis_y_position_label = serializers.CharField(
        source="get_axis_y_position_display", read_only=True
    )
    driver_states = ScenarioDriverStateSerializer(many=True, read_only=True)
    reviews = ScenarioReviewSerializer(many=True, read_only=True)
    review_summary = serializers.SerializerMethodField()
    wind_tunnel_assessments = WindTunnelAssessmentSerializer(many=True, read_only=True)
    implication_links = ScenarioImplicationLinkSerializer(many=True, read_only=True)
    signpost_links = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Scenario
        fields = [
            "id",
            "scenario_set_id",
            "title",
            "code",
            "axis_x_position",
            "axis_x_position_label",
            "axis_y_position",
            "axis_y_position_label",
            "headline",
            "narrative",
            "key_assumptions",
            "opportunities",
            "threats",
            "status",
            "status_label",
            "created_by",
            "driver_states",
            "reviews",
            "review_summary",
            "wind_tunnel_assessments",
            "implication_links",
            "signpost_links",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_review_summary(self, obj: Scenario):
        reviews = list(obj.reviews.all())
        if not reviews:
            return {
                "review_count": 0,
                "plausibility": None,
                "internal_consistency": None,
                "distinctiveness": None,
                "usefulness": None,
                "confidence": None,
                "confidence_range": None,
            }
        confidences = [item.confidence for item in reviews]
        return {
            "review_count": len(reviews),
            "plausibility": round(mean(item.plausibility for item in reviews), 2),
            "internal_consistency": round(mean(item.internal_consistency for item in reviews), 2),
            "distinctiveness": round(mean(item.distinctiveness for item in reviews), 2),
            "usefulness": round(mean(item.usefulness for item in reviews), 2),
            "confidence": round(mean(confidences), 2),
            "confidence_range": max(confidences) - min(confidences),
        }

    def get_signpost_links(self, obj: Scenario):
        return [
            {
                "id": str(link.id),
                "signpost_id": str(link.signpost_id),
                "signpost_title": link.signpost.title,
                "relationship": link.relationship,
                "relationship_label": link.get_relationship_display(),
                "rationale": link.rationale,
            }
            for link in obj.signpost_links.all()
        ]

    def get_can_edit(self, obj: Scenario) -> bool:
        request = self.context.get("request")
        scenario_set = obj.scenario_set
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=scenario_set.canvas.organisation,
                created_by_id=obj.created_by_id,
                owner_id=scenario_set.owner_id,
            )
            and scenario_set.canvas.status != "archived"
            and scenario_set.status != ScenarioSet.Status.ARCHIVED
        )


class ScenarioWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    code = serializers.CharField(max_length=40, trim_whitespace=True)
    axis_x_position = serializers.ChoiceField(choices=Scenario.Position.choices)
    axis_y_position = serializers.ChoiceField(choices=Scenario.Position.choices)
    headline = serializers.CharField(max_length=320, trim_whitespace=True)
    narrative = serializers.CharField(max_length=20000, trim_whitespace=True)
    key_assumptions = serializers.CharField(max_length=12000, trim_whitespace=True)
    opportunities = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    threats = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=Scenario.Status.choices,
        required=False,
        default=Scenario.Status.DRAFT,
    )


class ScenarioPatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    code = serializers.CharField(max_length=40, trim_whitespace=True, required=False)
    headline = serializers.CharField(max_length=320, trim_whitespace=True, required=False)
    narrative = serializers.CharField(max_length=20000, trim_whitespace=True, required=False)
    key_assumptions = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    opportunities = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    threats = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(choices=Scenario.Status.choices, required=False)


class ScenarioDriverStateWriteSerializer(StrictSerializer):
    driver_id = serializers.UUIDField()
    state = serializers.ChoiceField(choices=ScenarioDriverState.State.choices)
    salience = serializers.IntegerField(min_value=1, max_value=5, default=3)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)


class ScenarioReviewWriteSerializer(StrictSerializer):
    plausibility = serializers.IntegerField(min_value=1, max_value=5)
    internal_consistency = serializers.IntegerField(min_value=1, max_value=5)
    distinctiveness = serializers.IntegerField(min_value=1, max_value=5)
    usefulness = serializers.IntegerField(min_value=1, max_value=5)
    confidence = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )


class WindTunnelAssessmentWriteSerializer(StrictSerializer):
    option_id = serializers.UUIDField()
    verdict = serializers.ChoiceField(choices=WindTunnelAssessment.Verdict.choices)
    desirability = serializers.IntegerField(min_value=1, max_value=5)
    feasibility = serializers.IntegerField(min_value=1, max_value=5)
    resilience = serializers.IntegerField(min_value=1, max_value=5)
    rationale = serializers.CharField(max_length=12000, trim_whitespace=True)
    conditions_for_success = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    vulnerabilities = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    mitigations = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )


class ScenarioSignpostLinkWriteSerializer(StrictSerializer):
    scenario_id = serializers.UUIDField()
    relationship = serializers.ChoiceField(choices=ScenarioSignpost.Relationship.choices)
    rationale = serializers.CharField(max_length=4000, trim_whitespace=True)


class SignpostWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    indicator = serializers.CharField(max_length=500, trim_whitespace=True)
    threshold = serializers.CharField(max_length=500, trim_whitespace=True)
    direction = serializers.ChoiceField(choices=Signpost.Direction.choices)
    review_cadence = serializers.ChoiceField(choices=Signpost.Cadence.choices)
    source_notes = serializers.CharField(
        max_length=12000, trim_whitespace=True, required=False, allow_blank=True
    )
    owner_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=Signpost.Status.choices,
        required=False,
        default=Signpost.Status.ACTIVE,
    )
    scenario_links = ScenarioSignpostLinkWriteSerializer(many=True, required=False, default=list)

    def validate_scenario_links(self, value):  # type: ignore[no-untyped-def]
        ids = [str(item["scenario_id"]) for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Choose each scenario only once.")
        return value


class SignpostObservationSerializer(serializers.ModelSerializer):
    assessment_label = serializers.CharField(source="get_assessment_display", read_only=True)
    source_id = serializers.UUIDField(read_only=True, allow_null=True)
    source_title = serializers.CharField(source="source.title", read_only=True, allow_null=True)
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = SignpostObservation
        fields = [
            "id",
            "signpost_id",
            "observed_on",
            "value",
            "assessment",
            "assessment_label",
            "evidence",
            "source_id",
            "source_title",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SignpostSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    direction_label = serializers.CharField(source="get_direction_display", read_only=True)
    review_cadence_label = serializers.CharField(
        source="get_review_cadence_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    scenario_links = serializers.SerializerMethodField()
    observations = SignpostObservationSerializer(many=True, read_only=True)
    latest_observation = serializers.SerializerMethodField()
    assumption_links = serializers.SerializerMethodField()
    risk_links = serializers.SerializerMethodField()

    class Meta:
        model = Signpost
        fields = [
            "id",
            "scenario_set_id",
            "title",
            "description",
            "indicator",
            "threshold",
            "direction",
            "direction_label",
            "review_cadence",
            "review_cadence_label",
            "source_notes",
            "owner",
            "created_by",
            "status",
            "status_label",
            "scenario_links",
            "observations",
            "latest_observation",
            "assumption_links",
            "risk_links",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_scenario_links(self, obj: Signpost):
        return [
            {
                "id": str(link.id),
                "scenario_id": str(link.scenario_id),
                "scenario_title": link.scenario.title,
                "relationship": link.relationship,
                "relationship_label": link.get_relationship_display(),
                "rationale": link.rationale,
            }
            for link in obj.scenario_links.all()
        ]

    def get_assumption_links(self, obj: Signpost):
        return [
            {
                "id": str(link.id),
                "assumption_id": str(link.assumption_id),
                "assumption_statement": link.assumption.statement,
                "rationale": link.rationale,
            }
            for link in obj.assumption_links.select_related("assumption").all()
        ]

    def get_risk_links(self, obj: Signpost):
        return [
            {
                "id": str(link.id),
                "risk_id": str(link.risk_id),
                "risk_title": link.risk.title,
                "rationale": link.rationale,
            }
            for link in obj.risk_links.select_related("risk").all()
        ]

    def get_latest_observation(self, obj: Signpost):
        observations = list(obj.observations.all())
        if not observations:
            return None
        item = observations[0]
        return {
            "id": str(item.id),
            "observed_on": item.observed_on,
            "value": item.value,
            "assessment": item.assessment,
            "assessment_label": item.get_assessment_display(),
        }


class SignpostObservationWriteSerializer(StrictSerializer):
    observed_on = serializers.DateField()
    value = serializers.CharField(max_length=500, trim_whitespace=True)
    assessment = serializers.ChoiceField(choices=SignpostObservation.Assessment.choices)
    evidence = serializers.CharField(max_length=12000, trim_whitespace=True)
    source_id = serializers.UUIDField(required=False, allow_null=True)


class ScenarioImplicationLinkWriteSerializer(StrictSerializer):
    implication_id = serializers.UUIDField()
    effect = serializers.ChoiceField(choices=ScenarioImplicationLink.Effect.choices)
    rationale = serializers.CharField(max_length=12000, trim_whitespace=True)


class SignpostAssumptionLinkWriteSerializer(StrictSerializer):
    assumption_id = serializers.UUIDField()
    rationale = serializers.CharField(max_length=4000, trim_whitespace=True)


class SignpostRiskLinkWriteSerializer(StrictSerializer):
    risk_id = serializers.UUIDField()
    rationale = serializers.CharField(max_length=4000, trim_whitespace=True)


class ScenarioSetWorkspaceSerializer(ScenarioSetSerializer):
    scenarios = ScenarioSerializer(many=True, read_only=True)
    signposts = SignpostSerializer(many=True, read_only=True)
    decision_options = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta(ScenarioSetSerializer.Meta):
        fields = ScenarioSetSerializer.Meta.fields + [
            "scenarios",
            "signposts",
            "decision_options",
            "summary",
        ]

    def get_decision_options(self, obj: ScenarioSet):
        if not obj.linked_decision_id:
            return []
        return [
            {
                "id": str(option.id),
                "title": option.title,
                "description": option.description,
                "status": option.status,
                "is_status_quo": option.is_status_quo,
            }
            for option in obj.linked_decision.options.filter(status="active").order_by(
                "-is_status_quo", "title"
            )
        ]

    def get_summary(self, obj: ScenarioSet):
        scenarios = list(obj.scenarios.all())
        signposts = list(obj.signposts.all())
        assessments = [
            assessment
            for scenario in scenarios
            for assessment in scenario.wind_tunnel_assessments.all()
        ]
        return {
            "scenario_count": len(scenarios),
            "review_count": sum(len(scenario.reviews.all()) for scenario in scenarios),
            "assessment_count": len(assessments),
            "robust_assessment_count": sum(
                item.verdict == WindTunnelAssessment.Verdict.ROBUST for item in assessments
            ),
            "active_signpost_count": sum(
                item.status == Signpost.Status.ACTIVE for item in signposts
            ),
            "observation_count": sum(len(signpost.observations.all()) for signpost in signposts),
        }
