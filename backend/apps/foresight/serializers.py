"""REST contracts for foresight records."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import FeedSubscription, Signal, Source, SourceAttachment, Watchlist
from .policies import can_contribute, can_manage_record


class FeedSubscriptionSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = FeedSubscription
        fields = [
            "id", "organisation_id", "name", "feed_url", "owner", "created_by",
            "is_active", "last_checked_at", "last_success_at", "last_error",
            "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: FeedSubscription) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
        )


class FeedSubscriptionWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    feed_url = serializers.URLField(max_length=1200)
    owner_id = serializers.UUIDField(required=False)


class SourceAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = DecisionUserSerializer(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = SourceAttachment
        fields = [
            "id", "original_name", "content_type", "size_bytes", "sha256",
            "uploaded_by", "created_at", "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj: SourceAttachment) -> str:
        return f"/api/v1/foresight/attachments/{obj.id}/download/"


class SourceSerializer(serializers.ModelSerializer):
    created_by = DecisionUserSerializer(read_only=True)
    feed_name = serializers.CharField(source="feed.name", read_only=True, default=None)
    attachments = SourceAttachmentSerializer(many=True, read_only=True)
    source_type_label = serializers.CharField(source="get_source_type_display", read_only=True)
    credibility_label = serializers.CharField(source="get_credibility_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Source
        fields = [
            "id", "organisation_id", "feed_id", "feed_name", "external_id", "title", "source_type", "source_type_label",
            "author", "publisher", "published_on", "source_url", "reference",
            "credibility", "credibility_label", "credibility_rationale", "notes",
            "status", "status_label", "supersedes_id", "created_by", "attachments",
            "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: Source) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.organisation,
                created_by_id=obj.created_by_id,
            )
        )


class SourceWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=300, trim_whitespace=True)
    source_type = serializers.ChoiceField(choices=Source.SourceType.choices)
    author = serializers.CharField(max_length=240, trim_whitespace=True, allow_blank=True, required=False, default="")
    publisher = serializers.CharField(max_length=240, trim_whitespace=True, allow_blank=True, required=False, default="")
    published_on = serializers.DateField(required=False, allow_null=True)
    source_url = serializers.URLField(max_length=1200, allow_blank=True, required=False, default="")
    reference = serializers.CharField(max_length=800, trim_whitespace=True, allow_blank=True, required=False, default="")
    credibility = serializers.ChoiceField(choices=Source.Credibility.choices, required=False, default=Source.Credibility.UNASSESSED)
    credibility_rationale = serializers.CharField(max_length=8000, trim_whitespace=True, allow_blank=True, required=False, default="")
    notes = serializers.CharField(max_length=12000, trim_whitespace=True, allow_blank=True, required=False, default="")
    status = serializers.ChoiceField(choices=Source.Status.choices, required=False, default=Source.Status.ACTIVE)
    supersedes_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs.get("source_url") and not attrs.get("reference"):
            raise serializers.ValidationError(
                {"reference": "Provide a URL or reference now; a file may be attached after creation."}
            )
        return attrs


class SourcePatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=300, trim_whitespace=True, required=False)
    source_type = serializers.ChoiceField(choices=Source.SourceType.choices, required=False)
    author = serializers.CharField(max_length=240, trim_whitespace=True, allow_blank=True, required=False)
    publisher = serializers.CharField(max_length=240, trim_whitespace=True, allow_blank=True, required=False)
    published_on = serializers.DateField(required=False, allow_null=True)
    source_url = serializers.URLField(max_length=1200, allow_blank=True, required=False)
    reference = serializers.CharField(max_length=800, trim_whitespace=True, allow_blank=True, required=False)
    credibility = serializers.ChoiceField(choices=Source.Credibility.choices, required=False)
    credibility_rationale = serializers.CharField(max_length=8000, trim_whitespace=True, allow_blank=True, required=False)
    notes = serializers.CharField(max_length=12000, trim_whitespace=True, allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=Source.Status.choices, required=False)
    supersedes_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class SignalSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    source_title = serializers.CharField(source="source.title", read_only=True, default=None)
    steep_label = serializers.CharField(source="get_steep_category_display", read_only=True)
    horizon_label = serializers.CharField(source="get_time_horizon_display", read_only=True)
    maturity_label = serializers.CharField(source="get_maturity_display", read_only=True)
    polarity_label = serializers.CharField(source="get_polarity_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_score = serializers.IntegerField(read_only=True)
    linked_decisions = serializers.SerializerMethodField()
    watchlists = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = [
            "id", "organisation_id", "source_id", "source_title", "title", "summary",
            "future_implication", "steep_category", "steep_label", "time_horizon",
            "horizon_label", "maturity", "maturity_label", "polarity", "polarity_label",
            "geography", "domain", "impact", "uncertainty", "priority_score", "status",
            "status_label", "owner", "created_by", "last_reviewed_at", "linked_decisions",
            "watchlists", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_linked_decisions(self, obj: Signal):
        return [
            {"id": str(link.decision_id), "title": link.decision.title, "relevance": link.relevance}
            for link in obj.decision_links.all()
        ]

    def get_watchlists(self, obj: Signal):
        return [{"id": str(item.id), "name": item.name} for item in obj.watchlists.all()]

    def get_can_edit(self, obj: Signal) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
        )


class SignalWriteSerializer(StrictSerializer):
    source_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=280, trim_whitespace=True)
    summary = serializers.CharField(max_length=12000, trim_whitespace=True)
    future_implication = serializers.CharField(max_length=12000, trim_whitespace=True)
    steep_category = serializers.ChoiceField(choices=Signal.SteepCategory.choices)
    time_horizon = serializers.ChoiceField(choices=Signal.TimeHorizon.choices)
    maturity = serializers.ChoiceField(choices=Signal.Maturity.choices)
    polarity = serializers.ChoiceField(choices=Signal.Polarity.choices, required=False, default=Signal.Polarity.UNCLEAR)
    geography = serializers.CharField(max_length=160, trim_whitespace=True, allow_blank=True, required=False, default="")
    domain = serializers.CharField(max_length=160, trim_whitespace=True, allow_blank=True, required=False, default="")
    impact = serializers.IntegerField(min_value=1, max_value=5)
    uncertainty = serializers.IntegerField(min_value=1, max_value=5)
    status = serializers.ChoiceField(choices=Signal.Status.choices, required=False, default=Signal.Status.DRAFT)
    owner_id = serializers.UUIDField(required=False)


class SignalPatchSerializer(StrictSerializer):
    source_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=280, trim_whitespace=True, required=False)
    summary = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    future_implication = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    steep_category = serializers.ChoiceField(choices=Signal.SteepCategory.choices, required=False)
    time_horizon = serializers.ChoiceField(choices=Signal.TimeHorizon.choices, required=False)
    maturity = serializers.ChoiceField(choices=Signal.Maturity.choices, required=False)
    polarity = serializers.ChoiceField(choices=Signal.Polarity.choices, required=False)
    geography = serializers.CharField(max_length=160, trim_whitespace=True, allow_blank=True, required=False)
    domain = serializers.CharField(max_length=160, trim_whitespace=True, allow_blank=True, required=False)
    impact = serializers.IntegerField(min_value=1, max_value=5, required=False)
    uncertainty = serializers.IntegerField(min_value=1, max_value=5, required=False)
    status = serializers.ChoiceField(choices=Signal.Status.choices, required=False)
    owner_id = serializers.UUIDField(required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class SignalDecisionLinkSerializer(StrictSerializer):
    decision_id = serializers.UUIDField()
    relevance = serializers.CharField(max_length=8000, trim_whitespace=True)


class WatchlistSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    signal_count = serializers.IntegerField(read_only=True, default=0)
    signals = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Watchlist
        fields = [
            "id", "organisation_id", "name", "description", "owner", "created_by",
            "is_active", "signal_count", "signals", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_signals(self, obj: Watchlist):
        return [
            {
                "id": str(signal.id),
                "title": signal.title,
                "steep_category": signal.steep_category,
                "time_horizon": signal.time_horizon,
                "priority_score": signal.priority_score,
            }
            for signal in obj.signals.all()
        ]

    def get_can_edit(self, obj: Watchlist) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_record(
                actor=request.user,
                organisation=obj.organisation,
                created_by_id=obj.created_by_id,
                owner_id=obj.owner_id,
            )
        )


class WatchlistWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=180, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, allow_blank=True, required=False, default="")
    owner_id = serializers.UUIDField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)


class WatchlistPatchSerializer(StrictSerializer):
    name = serializers.CharField(max_length=180, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, allow_blank=True, required=False)
    owner_id = serializers.UUIDField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class WatchlistSignalSerializer(StrictSerializer):
    signal_id = serializers.UUIDField()
    note = serializers.CharField(max_length=500, trim_whitespace=True, allow_blank=True, required=False, default="")
