"""REST contracts for foresight canvases and systems mapping."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import (
    CausalRelationship,
    Driver,
    FeedbackLoop,
    ForesightCanvas,
    FuturesWheelConsequence,
    StrategicImplication,
    SystemStakeholder,
    ThreeHorizonItem,
)
from .policies import can_manage_record
from .scenario_serializers import ScenarioSetSerializer


class CanvasSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    driver_count = serializers.IntegerField(read_only=True, default=0)
    implication_count = serializers.IntegerField(read_only=True, default=0)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ForesightCanvas
        fields = [
            "id", "organisation_id", "title", "focal_question", "scope", "horizon_year",
            "owner", "created_by", "status", "status_label", "driver_count",
            "implication_count", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: ForesightCanvas) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
            and obj.status != ForesightCanvas.Status.ARCHIVED
        )


class CanvasWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    focal_question = serializers.CharField(max_length=12000, trim_whitespace=True)
    scope = serializers.CharField(max_length=12000, trim_whitespace=True)
    horizon_year = serializers.IntegerField(min_value=2000, max_value=2200)
    owner_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=ForesightCanvas.Status.choices, required=False, default=ForesightCanvas.Status.DRAFT
    )


class CanvasPatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    focal_question = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    scope = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    horizon_year = serializers.IntegerField(min_value=2000, max_value=2200, required=False)
    owner_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=ForesightCanvas.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class DriverSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    driver_type_label = serializers.CharField(source="get_driver_type_display", read_only=True)
    steep_label = serializers.CharField(source="get_steep_category_display", read_only=True)
    direction_label = serializers.CharField(source="get_direction_display", read_only=True)
    attention_score = serializers.IntegerField(read_only=True)
    linked_signals = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            "id", "canvas_id", "title", "description", "driver_type", "driver_type_label",
            "steep_category", "steep_label", "direction", "direction_label", "impact",
            "uncertainty", "attention_score", "owner", "created_by", "is_active",
            "linked_signals", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_linked_signals(self, obj: Driver):
        return [
            {
                "id": str(link.signal_id),
                "title": link.signal.title,
                "rationale": link.rationale,
            }
            for link in obj.signal_links.all()
        ]

    def get_can_edit(self, obj: Driver) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.canvas.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
            and obj.canvas.status != ForesightCanvas.Status.ARCHIVED
        )


class DriverWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    driver_type = serializers.ChoiceField(choices=Driver.DriverType.choices)
    steep_category = serializers.ChoiceField(choices=Driver._meta.get_field("steep_category").choices)
    direction = serializers.ChoiceField(
        choices=Driver.Direction.choices, required=False, default=Driver.Direction.UNCLEAR
    )
    impact = serializers.IntegerField(min_value=1, max_value=5)
    uncertainty = serializers.IntegerField(min_value=1, max_value=5)
    owner_id = serializers.UUIDField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)


class DriverPatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    driver_type = serializers.ChoiceField(choices=Driver.DriverType.choices, required=False)
    steep_category = serializers.ChoiceField(
        choices=Driver._meta.get_field("steep_category").choices, required=False
    )
    direction = serializers.ChoiceField(choices=Driver.Direction.choices, required=False)
    impact = serializers.IntegerField(min_value=1, max_value=5, required=False)
    uncertainty = serializers.IntegerField(min_value=1, max_value=5, required=False)
    owner_id = serializers.UUIDField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class DriverSignalWriteSerializer(StrictSerializer):
    signal_id = serializers.UUIDField()
    rationale = serializers.CharField(max_length=1000, trim_whitespace=True)


class StakeholderSerializer(serializers.ModelSerializer):
    stakeholder_type_label = serializers.CharField(source="get_stakeholder_type_display", read_only=True)
    stance_label = serializers.CharField(source="get_stance_display", read_only=True)
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = SystemStakeholder
        fields = [
            "id", "canvas_id", "name", "stakeholder_type", "stakeholder_type_label",
            "role", "interests", "influence", "exposure", "stance", "stance_label",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = fields


class StakeholderWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=240, trim_whitespace=True)
    stakeholder_type = serializers.ChoiceField(choices=SystemStakeholder.StakeholderType.choices)
    role = serializers.CharField(max_length=12000, trim_whitespace=True)
    interests = serializers.CharField(max_length=12000, trim_whitespace=True)
    influence = serializers.IntegerField(min_value=1, max_value=5)
    exposure = serializers.IntegerField(min_value=1, max_value=5)
    stance = serializers.ChoiceField(
        choices=SystemStakeholder.Stance.choices,
        required=False,
        default=SystemStakeholder.Stance.UNCLEAR,
    )


class RelationshipSerializer(serializers.ModelSerializer):
    source_title = serializers.CharField(source="source_driver.title", read_only=True)
    target_title = serializers.CharField(source="target_driver.title", read_only=True)
    polarity_label = serializers.CharField(source="get_polarity_display", read_only=True)
    delay_label = serializers.CharField(source="get_delay_display", read_only=True)
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = CausalRelationship
        fields = [
            "id", "canvas_id", "source_driver_id", "source_title", "target_driver_id",
            "target_title", "polarity", "polarity_label", "strength", "delay",
            "delay_label", "rationale", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = fields


class RelationshipWriteSerializer(StrictSerializer):
    source_driver_id = serializers.UUIDField()
    target_driver_id = serializers.UUIDField()
    polarity = serializers.ChoiceField(choices=CausalRelationship.Polarity.choices)
    strength = serializers.IntegerField(min_value=1, max_value=5)
    delay = serializers.ChoiceField(
        choices=CausalRelationship.Delay.choices,
        required=False,
        default=CausalRelationship.Delay.UNKNOWN,
    )
    rationale = serializers.CharField(max_length=12000, trim_whitespace=True)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if attrs["source_driver_id"] == attrs["target_driver_id"]:
            raise serializers.ValidationError("A driver cannot cause itself.")
        return attrs


class FeedbackLoopSerializer(serializers.ModelSerializer):
    loop_type_label = serializers.CharField(source="get_loop_type_display", read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    drivers = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackLoop
        fields = [
            "id",
            "canvas_id",
            "name",
            "description",
            "loop_type",
            "loop_type_label",
            "drivers",
            "rationale",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_drivers(self, obj: FeedbackLoop):  # type: ignore[no-untyped-def]
        return [
            {"id": str(link.driver_id), "title": link.driver.title}
            for link in obj.driver_links.all()
        ]


class FeedbackLoopWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=240, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    loop_type = serializers.ChoiceField(choices=FeedbackLoop.LoopType.choices)
    driver_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=2, allow_empty=False
    )
    rationale = serializers.CharField(max_length=12000, trim_whitespace=True)


class ConsequenceSerializer(serializers.ModelSerializer):
    originating_driver_title = serializers.CharField(
        source="originating_driver.title", read_only=True, default=None
    )
    parent_title = serializers.CharField(source="parent.title", read_only=True, default=None)
    consequence_type_label = serializers.CharField(
        source="get_consequence_type_display", read_only=True
    )
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = FuturesWheelConsequence
        fields = [
            "id", "canvas_id", "originating_driver_id", "originating_driver_title",
            "parent_id", "parent_title", "title", "description", "order",
            "consequence_type", "consequence_type_label", "likelihood", "impact",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = fields


class ConsequenceWriteSerializer(StrictSerializer):
    originating_driver_id = serializers.UUIDField(required=False, allow_null=True)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=260, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    consequence_type = serializers.ChoiceField(
        choices=FuturesWheelConsequence.ConsequenceType.choices,
        required=False,
        default=FuturesWheelConsequence.ConsequenceType.UNCLEAR,
    )
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)


class HorizonItemSerializer(serializers.ModelSerializer):
    horizon_label = serializers.CharField(source="get_horizon_display", read_only=True)
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = ThreeHorizonItem
        fields = [
            "id", "canvas_id", "horizon", "horizon_label", "title", "description",
            "evidence", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = fields


class HorizonItemWriteSerializer(StrictSerializer):
    horizon = serializers.ChoiceField(choices=ThreeHorizonItem.Horizon.choices)
    title = serializers.CharField(max_length=260, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    evidence = serializers.CharField(
        max_length=12000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )


class ImplicationSerializer(serializers.ModelSerializer):
    implication_type_label = serializers.CharField(source="get_implication_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    linked_decision_title = serializers.CharField(
        source="linked_decision.title", read_only=True, default=None
    )
    drivers = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = StrategicImplication
        fields = [
            "id", "canvas_id", "title", "description", "implication_type",
            "implication_type_label", "priority", "owner", "linked_decision_id",
            "linked_decision_title", "drivers", "status", "status_label", "created_by",
            "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_drivers(self, obj: StrategicImplication):
        return [{"id": str(driver.id), "title": driver.title} for driver in obj.drivers.all()]

    def get_can_edit(self, obj: StrategicImplication) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.canvas.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
            and obj.canvas.status != ForesightCanvas.Status.ARCHIVED
        )


class ImplicationWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=260, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    implication_type = serializers.ChoiceField(choices=StrategicImplication.ImplicationType.choices)
    priority = serializers.IntegerField(min_value=1, max_value=5)
    owner_id = serializers.UUIDField(required=False)
    linked_decision_id = serializers.UUIDField(required=False, allow_null=True)
    driver_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True, default=list
    )
    status = serializers.ChoiceField(
        choices=StrategicImplication.Status.choices,
        required=False,
        default=StrategicImplication.Status.OPEN,
    )


class ImplicationPatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=260, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    implication_type = serializers.ChoiceField(
        choices=StrategicImplication.ImplicationType.choices, required=False
    )
    priority = serializers.IntegerField(min_value=1, max_value=5, required=False)
    owner_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=StrategicImplication.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class CanvasWorkspaceSerializer(CanvasSerializer):
    drivers = DriverSerializer(many=True, read_only=True)
    stakeholders = StakeholderSerializer(many=True, read_only=True)
    relationships = RelationshipSerializer(many=True, read_only=True)
    feedback_loops = FeedbackLoopSerializer(many=True, read_only=True)
    consequences = ConsequenceSerializer(many=True, read_only=True)
    horizon_items = HorizonItemSerializer(many=True, read_only=True)
    implications = ImplicationSerializer(many=True, read_only=True)
    scenario_sets = ScenarioSetSerializer(many=True, read_only=True)
    summary = serializers.SerializerMethodField()

    class Meta(CanvasSerializer.Meta):
        fields = CanvasSerializer.Meta.fields + [
            "drivers", "stakeholders", "relationships", "feedback_loops",
            "consequences", "horizon_items", "implications", "scenario_sets", "summary",
        ]

    def get_summary(self, obj: ForesightCanvas):
        active_drivers = [item for item in obj.drivers.all() if item.is_active]
        return {
            "driver_count": len(active_drivers),
            "critical_uncertainty_count": sum(
                item.driver_type == Driver.DriverType.CRITICAL_UNCERTAINTY
                for item in active_drivers
            ),
            "high_attention_count": sum(item.attention_score >= 16 for item in active_drivers),
            "stakeholder_count": len(obj.stakeholders.all()),
            "relationship_count": len(obj.relationships.all()),
            "feedback_loop_count": len(obj.feedback_loops.all()),
            "scenario_set_count": len(obj.scenario_sets.all()),
            "open_implication_count": sum(
                item.status == StrategicImplication.Status.OPEN for item in obj.implications.all()
            ),
        }
