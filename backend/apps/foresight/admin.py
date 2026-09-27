from django.contrib import admin

from .models import (
    CausalRelationship,
    Driver,
    DriverSignal,
    FeedbackLoop,
    FeedbackLoopDriver,
    FeedSubscription,
    ForesightCanvas,
    FuturesWheelConsequence,
    ResearchClaim,
    ResearchClaimSource,
    Scenario,
    ScenarioDriverState,
    ScenarioImplicationLink,
    ScenarioReview,
    ScenarioSet,
    ScenarioSignpost,
    Signal,
    SignalDecisionLink,
    Signpost,
    SignpostObservation,
    Source,
    SourceAttachment,
    StrategicImplication,
    SystemStakeholder,
    ThreeHorizonItem,
    Watchlist,
    WatchlistSignal,
    WindTunnelAssessment,
)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "organisation", "source_type", "credibility", "status", "created_at")
    list_filter = ("source_type", "credibility", "status")
    search_fields = ("title", "author", "publisher", "reference")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("title", "organisation", "steep_category", "time_horizon", "maturity", "status")
    list_filter = ("steep_category", "time_horizon", "maturity", "status")
    search_fields = ("title", "summary", "future_implication")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ResearchClaim)
class ResearchClaimAdmin(admin.ModelAdmin):
    list_display = (
        "statement",
        "organisation",
        "state",
        "recommendation",
        "lifecycle_status",
        "review_due_on",
    )
    list_filter = ("state", "recommendation", "relevance", "lifecycle_status")
    search_fields = ("statement", "evidence_summary", "limitations")
    readonly_fields = ("id", "last_reviewed_at", "created_at", "updated_at")


admin.site.register(SourceAttachment)
admin.site.register(Watchlist)
admin.site.register(WatchlistSignal)
admin.site.register(SignalDecisionLink)
admin.site.register(ResearchClaimSource)

admin.site.register(FeedSubscription)

admin.site.register(ForesightCanvas)
admin.site.register(Driver)
admin.site.register(DriverSignal)
admin.site.register(SystemStakeholder)
admin.site.register(CausalRelationship)
admin.site.register(FeedbackLoop)
admin.site.register(FeedbackLoopDriver)
admin.site.register(FuturesWheelConsequence)
admin.site.register(ThreeHorizonItem)
admin.site.register(StrategicImplication)

admin.site.register(ScenarioSet)
admin.site.register(Scenario)
admin.site.register(ScenarioDriverState)
admin.site.register(ScenarioReview)
admin.site.register(WindTunnelAssessment)
admin.site.register(Signpost)
admin.site.register(ScenarioSignpost)
admin.site.register(SignpostObservation)
admin.site.register(ScenarioImplicationLink)
