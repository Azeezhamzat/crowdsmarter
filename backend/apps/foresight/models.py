"""Structured sources, signals, watchlists, and decision links."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


def source_attachment_path(instance: "SourceAttachment", filename: str) -> str:
    """Store private source files under stable tenant and source identifiers."""
    suffix = Path(filename).suffix.lower()
    return f"foresight/{instance.source.organisation_id}/{instance.source_id}/{instance.id}{suffix}"


class FeedSubscription(UUIDTimeStampedModel):
    """A manually synchronised RSS or Atom feed owned by one organisation."""

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="foresight_feeds"
    )
    name = models.CharField(max_length=200)
    feed_url = models.URLField(max_length=1200)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_foresight_feeds"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_foresight_feeds"
    )
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=1000, blank=True)
    etag = models.CharField(max_length=500, blank=True)
    last_modified = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["organisation", "feed_url"], name="unique_feed_url_per_org"),
            models.CheckConstraint(condition=~models.Q(name=""), name="foresight_feed_name_not_empty"),
        ]

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.feed_url = self.feed_url.strip()
        self.last_error = self.last_error.strip()
        if self.owner_id and not self.organisation.memberships.filter(user_id=self.owner_id, status="active").exists():
            raise ValidationError({"owner": "The owner must be an active organisation member."})

    def __str__(self) -> str:
        return self.name


class Source(UUIDTimeStampedModel):
    """An attributable source that can support signals and decision evidence."""

    class SourceType(models.TextChoices):
        RESEARCH = "research", "Research publication"
        NEWS = "news", "News or media"
        GOVERNMENT = "government", "Government or regulation"
        INTERNAL = "internal", "Internal organisational record"
        EXPERT = "expert", "Expert contribution"
        STAKEHOLDER = "stakeholder", "Stakeholder contribution"
        DATASET = "dataset", "Dataset"
        OTHER = "other", "Other"

    class Credibility(models.TextChoices):
        UNASSESSED = "unassessed", "Not assessed"
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUPERSEDED = "superseded", "Superseded"
        WITHDRAWN = "withdrawn", "Withdrawn"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="foresight_sources"
    )
    feed = models.ForeignKey(
        "foresight.FeedSubscription",
        on_delete=models.SET_NULL,
        related_name="imported_sources",
        null=True,
        blank=True,
    )
    external_id = models.CharField(max_length=500, blank=True)
    title = models.CharField(max_length=300)
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    author = models.CharField(max_length=240, blank=True)
    publisher = models.CharField(max_length=240, blank=True)
    published_on = models.DateField(null=True, blank=True)
    source_url = models.URLField(max_length=1200, blank=True)
    reference = models.CharField(max_length=800, blank=True)
    credibility = models.CharField(
        max_length=20, choices=Credibility.choices, default=Credibility.UNASSESSED
    )
    credibility_rationale = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    supersedes = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="superseded_by", null=True, blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_foresight_sources"
    )

    class Meta:
        ordering = ["-published_on", "-created_at", "title"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="foresight_source_title_not_empty"),
            models.CheckConstraint(
                condition=models.Q(source_type__in=["research", "news", "government", "internal", "expert", "stakeholder", "dataset", "other"]),
                name="foresight_source_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(credibility__in=["unassessed", "low", "moderate", "high"]),
                name="foresight_source_credibility_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "superseded", "withdrawn"]),
                name="foresight_source_status_valid",
            ),
            models.UniqueConstraint(
                fields=["feed", "external_id"],
                condition=~models.Q(external_id=""),
                name="unique_feed_external_source",
            ),
        ]
        indexes = [
            models.Index(fields=["organisation", "status", "source_type"], name="foresight_source_org_idx"),
            models.Index(fields=["organisation", "credibility"], name="foresight_source_cred_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.author = self.author.strip()
        self.publisher = self.publisher.strip()
        self.source_url = self.source_url.strip()
        self.reference = self.reference.strip()
        self.credibility_rationale = self.credibility_rationale.strip()
        self.notes = self.notes.strip()
        if not self.source_url and not self.reference and not self.attachments.exists():
            raise ValidationError("Provide a URL, reference, or attachment for this source.")
        if self.feed_id and self.feed.organisation_id != self.organisation_id:
            raise ValidationError({"feed": "The feed must share the source organisation."})
        if self.supersedes_id:
            if self.supersedes_id == self.id:
                raise ValidationError({"supersedes": "A source cannot supersede itself."})
            if self.supersedes.organisation_id != self.organisation_id:
                raise ValidationError({"supersedes": "The earlier source must share the organisation."})

    def __str__(self) -> str:
        return self.title


class SourceAttachment(UUIDTimeStampedModel):
    """A private, permission-controlled file attached to a source."""

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=source_attachment_path, max_length=600)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=160)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_source_attachments"
    )

    class Meta:
        ordering = ["created_at", "original_name"]
        constraints = [
            models.UniqueConstraint(fields=["source", "sha256"], name="unique_source_attachment_hash"),
        ]

    def __str__(self) -> str:
        return self.original_name


class Signal(UUIDTimeStampedModel):
    """An observed change with potential future implications."""

    class SteepCategory(models.TextChoices):
        SOCIAL = "social", "Social"
        TECHNOLOGICAL = "technological", "Technological"
        ECONOMIC = "economic", "Economic"
        ENVIRONMENTAL = "environmental", "Environmental"
        POLITICAL = "political", "Political"
        LEGAL = "legal", "Legal"
        ETHICAL = "ethical", "Ethical"

    class TimeHorizon(models.TextChoices):
        NEAR = "near", "Near term (0–2 years)"
        MEDIUM = "medium", "Medium term (3–5 years)"
        LONG = "long", "Long term (6+ years)"

    class Maturity(models.TextChoices):
        WEAK = "weak", "Weak signal"
        EMERGING = "emerging", "Emerging pattern"
        ESTABLISHED = "established", "Established trend"

    class Polarity(models.TextChoices):
        OPPORTUNITY = "opportunity", "Opportunity"
        THREAT = "threat", "Threat"
        BOTH = "both", "Opportunity and threat"
        UNCLEAR = "unclear", "Unclear"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEWED = "reviewed", "Reviewed"
        MONITORING = "monitoring", "Monitoring"
        RETIRED = "retired", "Retired"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="foresight_signals"
    )
    source = models.ForeignKey(
        Source, on_delete=models.PROTECT, related_name="signals", null=True, blank=True
    )
    title = models.CharField(max_length=280)
    summary = models.TextField()
    future_implication = models.TextField()
    steep_category = models.CharField(max_length=30, choices=SteepCategory.choices)
    time_horizon = models.CharField(max_length=20, choices=TimeHorizon.choices)
    maturity = models.CharField(max_length=20, choices=Maturity.choices)
    polarity = models.CharField(max_length=20, choices=Polarity.choices, default=Polarity.UNCLEAR)
    geography = models.CharField(max_length=160, blank=True)
    domain = models.CharField(max_length=160, blank=True)
    impact = models.PositiveSmallIntegerField(default=3)
    uncertainty = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_foresight_signals"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_foresight_signals"
    )
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_foresight_signals",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-impact", "-created_at", "title"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="foresight_signal_title_not_empty"),
            models.CheckConstraint(condition=models.Q(impact__gte=1, impact__lte=5), name="signal_impact_1_to_5"),
            models.CheckConstraint(condition=models.Q(uncertainty__gte=1, uncertainty__lte=5), name="signal_uncertainty_1_to_5"),
            models.CheckConstraint(
                condition=models.Q(steep_category__in=["social", "technological", "economic", "environmental", "political", "legal", "ethical"]),
                name="signal_steep_valid",
            ),
            models.CheckConstraint(condition=models.Q(time_horizon__in=["near", "medium", "long"]), name="signal_horizon_valid"),
            models.CheckConstraint(condition=models.Q(maturity__in=["weak", "emerging", "established"]), name="signal_maturity_valid"),
            models.CheckConstraint(condition=models.Q(polarity__in=["opportunity", "threat", "both", "unclear"]), name="signal_polarity_valid"),
            models.CheckConstraint(condition=models.Q(status__in=["draft", "reviewed", "monitoring", "retired"]), name="signal_status_valid"),
        ]
        indexes = [
            models.Index(fields=["organisation", "status", "steep_category"], name="signal_org_steep_idx"),
            models.Index(fields=["organisation", "time_horizon", "maturity"], name="signal_org_horizon_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.summary = self.summary.strip()
        self.future_implication = self.future_implication.strip()
        self.geography = self.geography.strip()
        self.domain = self.domain.strip()
        if self.source_id and self.source.organisation_id != self.organisation_id:
            raise ValidationError({"source": "The source must share the signal organisation."})
        for field_name in ("owner", "created_by"):
            user_id = getattr(self, f"{field_name}_id")
            if user_id and not self.organisation.memberships.filter(user_id=user_id, status="active").exists():
                raise ValidationError({field_name: "The person must be an active organisation member."})

    @property
    def priority_score(self) -> int:
        return self.impact * self.uncertainty

    def __str__(self) -> str:
        return self.title


class Watchlist(UUIDTimeStampedModel):
    """A curated set of signals monitored for one strategic concern."""

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="foresight_watchlists"
    )
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_foresight_watchlists"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_foresight_watchlists"
    )
    is_active = models.BooleanField(default=True)
    signals = models.ManyToManyField(Signal, through="WatchlistSignal", related_name="watchlists")

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["organisation", "name"], name="unique_watchlist_name_per_org"),
            models.CheckConstraint(condition=~models.Q(name=""), name="watchlist_name_not_empty"),
        ]

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.description = self.description.strip()
        if self.owner_id and not self.organisation.memberships.filter(user_id=self.owner_id, status="active").exists():
            raise ValidationError({"owner": "The owner must be an active organisation member."})

    def __str__(self) -> str:
        return self.name


class WatchlistSignal(UUIDTimeStampedModel):
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name="signal_links")
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name="watchlist_links")
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="added_watchlist_signals"
    )
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["watchlist", "signal"], name="unique_signal_per_watchlist"),
        ]

    def clean(self) -> None:
        super().clean()
        self.note = self.note.strip()
        if self.watchlist.organisation_id != self.signal.organisation_id:
            raise ValidationError("The signal and watchlist must share an organisation.")


class SignalDecisionLink(UUIDTimeStampedModel):
    """An explicit explanation of how a signal informs a decision."""

    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name="decision_links")
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="signal_links"
    )
    relevance = models.TextField()
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="linked_signal_decisions"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["signal", "decision"], name="unique_signal_decision_link"),
        ]

    def clean(self) -> None:
        super().clean()
        self.relevance = self.relevance.strip()
        if self.signal.organisation_id != self.decision.organisation_id:
            raise ValidationError("The signal and decision must share an organisation.")


class ForesightCanvas(UUIDTimeStampedModel):
    """A bounded systems-and-futures inquiry owned by one organisation."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETE = "complete", "Complete"
        ARCHIVED = "archived", "Archived"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="foresight_canvases"
    )
    title = models.CharField(max_length=240)
    focal_question = models.TextField()
    scope = models.TextField()
    horizon_year = models.PositiveSmallIntegerField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_foresight_canvases"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_foresight_canvases"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-updated_at", "title"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="foresight_canvas_title_not_empty"),
            models.CheckConstraint(
                condition=models.Q(horizon_year__gte=2000, horizon_year__lte=2200),
                name="foresight_canvas_horizon_year_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "active", "complete", "archived"]),
                name="foresight_canvas_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["organisation", "status", "horizon_year"], name="foresight_canvas_org_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.focal_question = self.focal_question.strip()
        self.scope = self.scope.strip()
        if not self.focal_question:
            raise ValidationError({"focal_question": "Define the inquiry's focal question."})
        if not self.scope:
            raise ValidationError({"scope": "Define the system boundary and scope."})
        for field_name in ("owner", "created_by"):
            user_id = getattr(self, f"{field_name}_id")
            if user_id and not self.organisation.memberships.filter(
                user_id=user_id, status="active"
            ).exists():
                raise ValidationError({field_name: "The person must be an active organisation member."})

    def __str__(self) -> str:
        return self.title


class Driver(UUIDTimeStampedModel):
    """A trend, force, uncertainty, predetermined element, or wild card."""

    class DriverType(models.TextChoices):
        TREND = "trend", "Trend"
        DRIVER = "driver", "Driver of change"
        CRITICAL_UNCERTAINTY = "critical_uncertainty", "Critical uncertainty"
        PREDETERMINED = "predetermined", "Predetermined element"
        WILD_CARD = "wild_card", "Wild card"

    class Direction(models.TextChoices):
        INCREASING = "increasing", "Increasing"
        DECREASING = "decreasing", "Decreasing"
        STABLE = "stable", "Stable"
        VOLATILE = "volatile", "Volatile"
        UNCLEAR = "unclear", "Unclear"

    canvas = models.ForeignKey(ForesightCanvas, on_delete=models.CASCADE, related_name="drivers")
    title = models.CharField(max_length=240)
    description = models.TextField()
    driver_type = models.CharField(max_length=30, choices=DriverType.choices)
    steep_category = models.CharField(max_length=30, choices=Signal.SteepCategory.choices)
    direction = models.CharField(max_length=20, choices=Direction.choices, default=Direction.UNCLEAR)
    impact = models.PositiveSmallIntegerField(default=3)
    uncertainty = models.PositiveSmallIntegerField(default=3)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_foresight_drivers"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_foresight_drivers"
    )
    is_active = models.BooleanField(default=True)
    signals = models.ManyToManyField(Signal, through="DriverSignal", related_name="drivers")

    class Meta:
        ordering = ["-impact", "-uncertainty", "title"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="foresight_driver_title_not_empty"),
            models.CheckConstraint(condition=models.Q(impact__gte=1, impact__lte=5), name="foresight_driver_impact_valid"),
            models.CheckConstraint(condition=models.Q(uncertainty__gte=1, uncertainty__lte=5), name="foresight_driver_uncertainty_valid"),
            models.CheckConstraint(
                condition=models.Q(driver_type__in=["trend", "driver", "critical_uncertainty", "predetermined", "wild_card"]),
                name="foresight_driver_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(direction__in=["increasing", "decreasing", "stable", "volatile", "unclear"]),
                name="foresight_driver_direction_valid",
            ),
            models.UniqueConstraint(fields=["canvas", "title"], name="unique_driver_title_per_canvas"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        if not self.description:
            raise ValidationError({"description": "Explain how this force may shape the system."})
        organisation = self.canvas.organisation
        for field_name in ("owner", "created_by"):
            user_id = getattr(self, f"{field_name}_id")
            if user_id and not organisation.memberships.filter(user_id=user_id, status="active").exists():
                raise ValidationError({field_name: "The person must be an active organisation member."})

    @property
    def attention_score(self) -> int:
        return self.impact * self.uncertainty

    def __str__(self) -> str:
        return self.title


class DriverSignal(UUIDTimeStampedModel):
    """An attributable explanation of how a signal supports a driver interpretation."""

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="signal_links")
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name="driver_links")
    rationale = models.CharField(max_length=1000)
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="linked_driver_signals"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["driver", "signal"], name="unique_signal_per_driver"),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if self.driver.canvas.organisation_id != self.signal.organisation_id:
            raise ValidationError("The signal and driver must share an organisation.")
        if not self.rationale:
            raise ValidationError({"rationale": "Explain how the signal informs this driver."})


class SystemStakeholder(UUIDTimeStampedModel):
    """An actor whose influence, exposure, or interests shape the focal system."""

    class StakeholderType(models.TextChoices):
        INTERNAL = "internal", "Internal"
        CUSTOMER = "customer", "Customer or beneficiary"
        PARTNER = "partner", "Partner"
        REGULATOR = "regulator", "Regulator or government"
        COMMUNITY = "community", "Community"
        COMPETITOR = "competitor", "Competitor"
        OTHER = "other", "Other"

    class Stance(models.TextChoices):
        SUPPORTIVE = "supportive", "Supportive"
        NEUTRAL = "neutral", "Neutral"
        RESISTANT = "resistant", "Resistant"
        MIXED = "mixed", "Mixed"
        UNCLEAR = "unclear", "Unclear"

    canvas = models.ForeignKey(ForesightCanvas, on_delete=models.CASCADE, related_name="stakeholders")
    name = models.CharField(max_length=240)
    stakeholder_type = models.CharField(max_length=30, choices=StakeholderType.choices)
    role = models.TextField()
    interests = models.TextField()
    influence = models.PositiveSmallIntegerField(default=3)
    exposure = models.PositiveSmallIntegerField(default=3)
    stance = models.CharField(max_length=20, choices=Stance.choices, default=Stance.UNCLEAR)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_system_stakeholders"
    )

    class Meta:
        ordering = ["-influence", "name"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=""), name="system_stakeholder_name_not_empty"),
            models.CheckConstraint(condition=models.Q(influence__gte=1, influence__lte=5), name="system_stakeholder_influence_valid"),
            models.CheckConstraint(condition=models.Q(exposure__gte=1, exposure__lte=5), name="system_stakeholder_exposure_valid"),
            models.UniqueConstraint(fields=["canvas", "name"], name="unique_stakeholder_name_per_canvas"),
        ]

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.role = self.role.strip()
        self.interests = self.interests.strip()
        if not self.role or not self.interests:
            raise ValidationError("Describe the stakeholder's role and interests.")

    def __str__(self) -> str:
        return self.name


class CausalRelationship(UUIDTimeStampedModel):
    """A documented causal relationship between two drivers."""

    class Polarity(models.TextChoices):
        REINFORCING = "reinforcing", "Reinforcing"
        BALANCING = "balancing", "Balancing"
        UNCERTAIN = "uncertain", "Uncertain"

    class Delay(models.TextChoices):
        IMMEDIATE = "immediate", "Immediate"
        SHORT = "short", "Short delay"
        MEDIUM = "medium", "Medium delay"
        LONG = "long", "Long delay"
        UNKNOWN = "unknown", "Unknown"

    canvas = models.ForeignKey(ForesightCanvas, on_delete=models.CASCADE, related_name="relationships")
    source_driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="outgoing_relationships")
    target_driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="incoming_relationships")
    polarity = models.CharField(max_length=20, choices=Polarity.choices)
    strength = models.PositiveSmallIntegerField(default=3)
    delay = models.CharField(max_length=20, choices=Delay.choices, default=Delay.UNKNOWN)
    rationale = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_causal_relationships"
    )

    class Meta:
        ordering = ["source_driver__title", "target_driver__title"]
        constraints = [
            models.CheckConstraint(condition=models.Q(strength__gte=1, strength__lte=5), name="causal_relationship_strength_valid"),
            models.CheckConstraint(condition=~models.Q(source_driver=models.F("target_driver")), name="causal_relationship_not_self"),
            models.UniqueConstraint(
                fields=["canvas", "source_driver", "target_driver"],
                name="unique_directed_relationship_per_canvas",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if self.source_driver.canvas_id != self.canvas_id or self.target_driver.canvas_id != self.canvas_id:
            raise ValidationError("Both drivers must belong to this canvas.")
        if not self.rationale:
            raise ValidationError({"rationale": "Explain the causal mechanism and evidence."})

class FeedbackLoop(UUIDTimeStampedModel):
    """A human-interpreted feedback structure grounded in connected drivers."""

    class LoopType(models.TextChoices):
        REINFORCING = "reinforcing", "Reinforcing"
        BALANCING = "balancing", "Balancing"
        MIXED = "mixed", "Mixed"
        UNCERTAIN = "uncertain", "Uncertain"

    canvas = models.ForeignKey(
        ForesightCanvas, on_delete=models.CASCADE, related_name="feedback_loops"
    )
    name = models.CharField(max_length=240)
    description = models.TextField()
    loop_type = models.CharField(max_length=20, choices=LoopType.choices)
    drivers = models.ManyToManyField(
        Driver,
        through="FeedbackLoopDriver",
        related_name="feedback_loops",
    )
    rationale = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_feedback_loops",
    )

    class Meta:
        ordering = ["loop_type", "name"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="feedback_loop_name_not_empty",
            ),
            models.UniqueConstraint(
                fields=["canvas", "name"],
                name="unique_feedback_loop_name_per_canvas",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.description = self.description.strip()
        self.rationale = self.rationale.strip()
        if not self.description:
            raise ValidationError({"description": "Describe the feedback behaviour."})
        if not self.rationale:
            raise ValidationError({"rationale": "Explain why this feedback loop is credible."})

    def __str__(self) -> str:
        return self.name


class FeedbackLoopDriver(UUIDTimeStampedModel):
    """One ordered driver in a human-interpreted feedback loop."""

    feedback_loop = models.ForeignKey(
        FeedbackLoop,
        on_delete=models.CASCADE,
        related_name="driver_links",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name="feedback_loop_links",
    )
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(position__gte=1),
                name="feedback_loop_driver_position_positive",
            ),
            models.UniqueConstraint(
                fields=["feedback_loop", "driver"],
                name="unique_driver_per_feedback_loop",
            ),
            models.UniqueConstraint(
                fields=["feedback_loop", "position"],
                name="unique_position_per_feedback_loop",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.driver.canvas_id != self.feedback_loop.canvas_id:
            raise ValidationError(
                "The feedback-loop driver must belong to the same canvas."
            )


class FuturesWheelConsequence(UUIDTimeStampedModel):
    """A first-, second-, or third-order consequence in a futures wheel."""

    class ConsequenceType(models.TextChoices):
        OPPORTUNITY = "opportunity", "Opportunity"
        THREAT = "threat", "Threat"
        MIXED = "mixed", "Mixed"
        UNCLEAR = "unclear", "Unclear"

    canvas = models.ForeignKey(ForesightCanvas, on_delete=models.CASCADE, related_name="consequences")
    originating_driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="consequences", null=True, blank=True
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", null=True, blank=True
    )
    title = models.CharField(max_length=260)
    description = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)
    consequence_type = models.CharField(
        max_length=20, choices=ConsequenceType.choices, default=ConsequenceType.UNCLEAR
    )
    likelihood = models.PositiveSmallIntegerField(default=3)
    impact = models.PositiveSmallIntegerField(default=3)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_futures_consequences"
    )

    class Meta:
        ordering = ["order", "-impact", "title"]
        constraints = [
            models.CheckConstraint(condition=models.Q(order__gte=1, order__lte=3), name="futures_consequence_order_valid"),
            models.CheckConstraint(condition=models.Q(likelihood__gte=1, likelihood__lte=5), name="futures_consequence_likelihood_valid"),
            models.CheckConstraint(condition=models.Q(impact__gte=1, impact__lte=5), name="futures_consequence_impact_valid"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        if not self.description:
            raise ValidationError({"description": "Explain why this consequence may occur."})
        if self.originating_driver_id and self.originating_driver.canvas_id != self.canvas_id:
            raise ValidationError({"originating_driver": "The driver must belong to this canvas."})
        if self.parent_id:
            if self.parent.canvas_id != self.canvas_id:
                raise ValidationError({"parent": "The parent consequence must belong to this canvas."})
            if self.order != self.parent.order + 1:
                raise ValidationError({"order": "A child consequence must be exactly one order beyond its parent."})
        elif self.order != 1:
            raise ValidationError({"order": "A consequence without a parent must be first-order."})


class ThreeHorizonItem(UUIDTimeStampedModel):
    """A structured item in a Three Horizons transition view."""

    class Horizon(models.TextChoices):
        H1 = "h1", "Horizon 1 — current system"
        H2 = "h2", "Horizon 2 — transition"
        H3 = "h3", "Horizon 3 — emerging future"

    canvas = models.ForeignKey(ForesightCanvas, on_delete=models.CASCADE, related_name="horizon_items")
    horizon = models.CharField(max_length=10, choices=Horizon.choices)
    title = models.CharField(max_length=260)
    description = models.TextField()
    evidence = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_three_horizon_items"
    )

    class Meta:
        ordering = ["horizon", "title"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="three_horizon_title_not_empty"),
            models.CheckConstraint(condition=models.Q(horizon__in=["h1", "h2", "h3"]), name="three_horizon_value_valid"),
            models.UniqueConstraint(fields=["canvas", "horizon", "title"], name="unique_horizon_item_per_canvas"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.evidence = self.evidence.strip()
        if not self.description:
            raise ValidationError({"description": "Explain this horizon item."})


class StrategicImplication(UUIDTimeStampedModel):
    """A traceable implication requiring interpretation, monitoring, or action."""

    class ImplicationType(models.TextChoices):
        OPPORTUNITY = "opportunity", "Opportunity"
        THREAT = "threat", "Threat"
        CAPABILITY = "capability", "Capability requirement"
        DECISION_REQUIREMENT = "decision_requirement", "Decision requirement"
        POLICY = "policy", "Policy implication"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ADDRESSED = "addressed", "Addressed"
        DISMISSED = "dismissed", "Dismissed"

    canvas = models.ForeignKey(ForesightCanvas, on_delete=models.CASCADE, related_name="implications")
    title = models.CharField(max_length=260)
    description = models.TextField()
    implication_type = models.CharField(max_length=30, choices=ImplicationType.choices)
    priority = models.PositiveSmallIntegerField(default=3)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_strategic_implications"
    )
    linked_decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.SET_NULL, related_name="foresight_implications", null=True, blank=True
    )
    drivers = models.ManyToManyField(Driver, related_name="implications", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_strategic_implications"
    )

    class Meta:
        ordering = ["-priority", "title"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="strategic_implication_title_not_empty"),
            models.CheckConstraint(condition=models.Q(priority__gte=1, priority__lte=5), name="strategic_implication_priority_valid"),
            models.CheckConstraint(condition=models.Q(status__in=["open", "addressed", "dismissed"]), name="strategic_implication_status_valid"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        if not self.description:
            raise ValidationError({"description": "Explain the strategic implication."})
        organisation = self.canvas.organisation
        if self.owner_id and not organisation.memberships.filter(user_id=self.owner_id, status="active").exists():
            raise ValidationError({"owner": "The owner must be an active organisation member."})
        if self.linked_decision_id and self.linked_decision.organisation_id != organisation.id:
            raise ValidationError({"linked_decision": "The decision must share the canvas organisation."})


class ScenarioSet(UUIDTimeStampedModel):
    """A governed two-axis scenario exercise grounded in one foresight canvas."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETE = "complete", "Complete"
        ARCHIVED = "archived", "Archived"

    canvas = models.ForeignKey(
        ForesightCanvas, on_delete=models.CASCADE, related_name="scenario_sets"
    )
    title = models.CharField(max_length=240)
    purpose = models.TextField()
    axis_x_driver = models.ForeignKey(
        Driver,
        on_delete=models.PROTECT,
        related_name="scenario_sets_as_x_axis",
    )
    axis_x_low_label = models.CharField(max_length=160)
    axis_x_high_label = models.CharField(max_length=160)
    axis_y_driver = models.ForeignKey(
        Driver,
        on_delete=models.PROTECT,
        related_name="scenario_sets_as_y_axis",
    )
    axis_y_low_label = models.CharField(max_length=160)
    axis_y_high_label = models.CharField(max_length=160)
    linked_decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.SET_NULL,
        related_name="foresight_scenario_sets",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_scenario_sets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_scenario_sets",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    class Meta:
        ordering = ["-updated_at", "title"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""), name="scenario_set_title_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(axis_x_driver=models.F("axis_y_driver")),
                name="scenario_set_axes_distinct",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["draft", "active", "complete", "archived"]
                ),
                name="scenario_set_status_valid",
            ),
            models.UniqueConstraint(
                fields=["canvas", "title"], name="unique_scenario_set_title_per_canvas"
            ),
        ]
        indexes = [
            models.Index(
                fields=["canvas", "status", "-updated_at"],
                name="scenario_set_canvas_idx",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.purpose = self.purpose.strip()
        self.axis_x_low_label = self.axis_x_low_label.strip()
        self.axis_x_high_label = self.axis_x_high_label.strip()
        self.axis_y_low_label = self.axis_y_low_label.strip()
        self.axis_y_high_label = self.axis_y_high_label.strip()
        if not self.purpose:
            raise ValidationError({"purpose": "Explain what this scenario exercise will test."})
        labels = {
            "axis_x_low_label": self.axis_x_low_label,
            "axis_x_high_label": self.axis_x_high_label,
            "axis_y_low_label": self.axis_y_low_label,
            "axis_y_high_label": self.axis_y_high_label,
        }
        for field_name, value in labels.items():
            if not value:
                raise ValidationError({field_name: "Provide a meaningful axis endpoint."})
        if self.axis_x_driver_id and self.axis_x_driver.canvas_id != self.canvas_id:
            raise ValidationError({"axis_x_driver": "Choose a driver from this canvas."})
        if self.axis_y_driver_id and self.axis_y_driver.canvas_id != self.canvas_id:
            raise ValidationError({"axis_y_driver": "Choose a driver from this canvas."})
        for field_name in ("axis_x_driver", "axis_y_driver"):
            driver = getattr(self, field_name, None)
            if driver and driver.driver_type != Driver.DriverType.CRITICAL_UNCERTAINTY:
                raise ValidationError(
                    {field_name: "Scenario axes must be critical uncertainties."}
                )
        if self.linked_decision_id:
            if self.linked_decision.organisation_id != self.canvas.organisation_id:
                raise ValidationError(
                    {"linked_decision": "The decision must share the canvas organisation."}
                )
        organisation = self.canvas.organisation
        for field_name in ("owner", "created_by"):
            user_id = getattr(self, f"{field_name}_id")
            if user_id and not organisation.memberships.filter(
                user_id=user_id, status="active"
            ).exists():
                raise ValidationError(
                    {field_name: "The person must be an active organisation member."}
                )

    def __str__(self) -> str:
        return self.title


class Scenario(UUIDTimeStampedModel):
    """One plausible world occupying a defined quadrant of a scenario set."""

    class Position(models.TextChoices):
        LOW = "low", "Low"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEWED = "reviewed", "Reviewed"

    scenario_set = models.ForeignKey(
        ScenarioSet, on_delete=models.CASCADE, related_name="scenarios"
    )
    title = models.CharField(max_length=240)
    code = models.CharField(max_length=40)
    axis_x_position = models.CharField(max_length=10, choices=Position.choices)
    axis_y_position = models.CharField(max_length=10, choices=Position.choices)
    headline = models.CharField(max_length=320)
    narrative = models.TextField()
    key_assumptions = models.TextField()
    opportunities = models.TextField(blank=True)
    threats = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_scenarios",
    )

    class Meta:
        ordering = ["axis_y_position", "axis_x_position", "title"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""), name="scenario_title_not_empty"
            ),
            models.CheckConstraint(
                condition=models.Q(axis_x_position__in=["low", "high"]),
                name="scenario_x_position_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(axis_y_position__in=["low", "high"]),
                name="scenario_y_position_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "reviewed"]),
                name="scenario_status_valid",
            ),
            models.UniqueConstraint(
                fields=["scenario_set", "axis_x_position", "axis_y_position"],
                name="unique_scenario_quadrant",
            ),
            models.UniqueConstraint(
                fields=["scenario_set", "code"], name="unique_scenario_code_per_set"
            ),
            models.UniqueConstraint(
                fields=["scenario_set", "title"], name="unique_scenario_title_per_set"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.code = self.code.strip().upper()
        self.headline = self.headline.strip()
        self.narrative = self.narrative.strip()
        self.key_assumptions = self.key_assumptions.strip()
        self.opportunities = self.opportunities.strip()
        self.threats = self.threats.strip()
        if not self.code:
            raise ValidationError({"code": "Provide a short scenario code."})
        if not self.headline:
            raise ValidationError({"headline": "Summarise this world in one line."})
        if not self.narrative:
            raise ValidationError({"narrative": "Describe the scenario world."})
        if not self.key_assumptions:
            raise ValidationError(
                {"key_assumptions": "Make the scenario assumptions explicit."}
            )

    def __str__(self) -> str:
        return f"{self.scenario_set}: {self.title}"


class ScenarioDriverState(UUIDTimeStampedModel):
    """A human interpretation of how a canvas driver behaves in one scenario."""

    class State(models.TextChoices):
        STRENGTHENING = "strengthening", "Strengthening"
        WEAKENING = "weakening", "Weakening"
        STABLE = "stable", "Stable"
        VOLATILE = "volatile", "Volatile"
        TRANSFORMED = "transformed", "Transformed"
        UNCERTAIN = "uncertain", "Uncertain"

    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, related_name="driver_states"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT, related_name="scenario_states"
    )
    state = models.CharField(max_length=20, choices=State.choices)
    salience = models.PositiveSmallIntegerField(default=3)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_scenario_driver_states",
    )

    class Meta:
        ordering = ["-salience", "driver__title"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(salience__gte=1, salience__lte=5),
                name="scenario_driver_salience_valid",
            ),
            models.UniqueConstraint(
                fields=["scenario", "driver"], name="unique_driver_state_per_scenario"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.description = self.description.strip()
        if self.driver_id and self.driver.canvas_id != self.scenario.scenario_set.canvas_id:
            raise ValidationError({"driver": "Choose a driver from the scenario canvas."})
        if not self.description:
            raise ValidationError({"description": "Explain the driver's scenario state."})


class ScenarioReview(UUIDTimeStampedModel):
    """One member's structured review of a scenario's quality and usefulness."""

    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="scenario_reviews",
    )
    plausibility = models.PositiveSmallIntegerField(default=3)
    internal_consistency = models.PositiveSmallIntegerField(default=3)
    distinctiveness = models.PositiveSmallIntegerField(default=3)
    usefulness = models.PositiveSmallIntegerField(default=3)
    confidence = models.PositiveSmallIntegerField(default=3)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(plausibility__gte=1, plausibility__lte=5),
                name="scenario_review_plausibility_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    internal_consistency__gte=1, internal_consistency__lte=5
                ),
                name="scenario_review_consistency_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(distinctiveness__gte=1, distinctiveness__lte=5),
                name="scenario_review_distinctiveness_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(usefulness__gte=1, usefulness__lte=5),
                name="scenario_review_usefulness_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__gte=1, confidence__lte=5),
                name="scenario_review_confidence_valid",
            ),
            models.UniqueConstraint(
                fields=["scenario", "reviewer"], name="unique_member_review_per_scenario"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.comment = self.comment.strip()
        organisation = self.scenario.scenario_set.canvas.organisation
        if self.reviewer_id and not organisation.memberships.filter(
            user_id=self.reviewer_id, status="active"
        ).exists():
            raise ValidationError(
                {"reviewer": "The reviewer must be an active organisation member."}
            )


class WindTunnelAssessment(UUIDTimeStampedModel):
    """A transparent test of one decision option against one scenario world."""

    class Verdict(models.TextChoices):
        ROBUST = "robust", "Robust"
        ADAPTABLE = "adaptable", "Adaptable with conditions"
        VULNERABLE = "vulnerable", "Vulnerable"
        INFEASIBLE = "infeasible", "Infeasible"
        UNCERTAIN = "uncertain", "Uncertain"

    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, related_name="wind_tunnel_assessments"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="scenario_assessments",
    )
    verdict = models.CharField(max_length=20, choices=Verdict.choices)
    desirability = models.PositiveSmallIntegerField(default=3)
    feasibility = models.PositiveSmallIntegerField(default=3)
    resilience = models.PositiveSmallIntegerField(default=3)
    rationale = models.TextField()
    conditions_for_success = models.TextField(blank=True)
    vulnerabilities = models.TextField(blank=True)
    mitigations = models.TextField(blank=True)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wind_tunnel_assessments",
    )

    class Meta:
        ordering = ["option__title", "scenario__title"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(desirability__gte=1, desirability__lte=5),
                name="wind_tunnel_desirability_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(feasibility__gte=1, feasibility__lte=5),
                name="wind_tunnel_feasibility_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(resilience__gte=1, resilience__lte=5),
                name="wind_tunnel_resilience_valid",
            ),
            models.UniqueConstraint(
                fields=["scenario", "option"], name="unique_option_assessment_per_scenario"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        self.conditions_for_success = self.conditions_for_success.strip()
        self.vulnerabilities = self.vulnerabilities.strip()
        self.mitigations = self.mitigations.strip()
        scenario_set = self.scenario.scenario_set
        if not scenario_set.linked_decision_id:
            raise ValidationError(
                {"option": "Link the scenario set to a decision before wind-tunnelling."}
            )
        if self.option_id and self.option.decision_id != scenario_set.linked_decision_id:
            raise ValidationError(
                {"option": "Choose an option from the scenario set's linked decision."}
            )
        if not self.rationale:
            raise ValidationError({"rationale": "Explain the assessment verdict."})

    @property
    def robustness_score(self) -> float:
        return round((self.desirability + self.feasibility + self.resilience) / 3, 2)


class Signpost(UUIDTimeStampedModel):
    """A monitored indicator that can support or challenge scenario worlds."""

    class Direction(models.TextChoices):
        ABOVE = "above", "Above threshold"
        BELOW = "below", "Below threshold"
        RISING = "rising", "Rising"
        FALLING = "falling", "Falling"
        CHANGE = "change", "Material change"
        QUALITATIVE = "qualitative", "Qualitative judgement"

    class Cadence(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        SEMIANNUAL = "semiannual", "Every six months"
        ANNUAL = "annual", "Annual"
        EVENT_DRIVEN = "event_driven", "Event-driven"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        RETIRED = "retired", "Retired"

    scenario_set = models.ForeignKey(
        ScenarioSet, on_delete=models.CASCADE, related_name="signposts"
    )
    title = models.CharField(max_length=240)
    description = models.TextField()
    indicator = models.CharField(max_length=500)
    threshold = models.CharField(max_length=500)
    direction = models.CharField(max_length=20, choices=Direction.choices)
    review_cadence = models.CharField(max_length=20, choices=Cadence.choices)
    source_notes = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_foresight_signposts",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_foresight_signposts",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    scenarios = models.ManyToManyField(
        Scenario, through="ScenarioSignpost", related_name="signposts"
    )

    class Meta:
        ordering = ["status", "title"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""), name="signpost_title_not_empty"
            ),
            models.UniqueConstraint(
                fields=["scenario_set", "title"], name="unique_signpost_title_per_set"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.indicator = self.indicator.strip()
        self.threshold = self.threshold.strip()
        self.source_notes = self.source_notes.strip()
        required = {
            "description": self.description,
            "indicator": self.indicator,
            "threshold": self.threshold,
        }
        for field_name, value in required.items():
            if not value:
                raise ValidationError({field_name: "This field is required."})
        organisation = self.scenario_set.canvas.organisation
        for field_name in ("owner", "created_by"):
            user_id = getattr(self, f"{field_name}_id")
            if user_id and not organisation.memberships.filter(
                user_id=user_id, status="active"
            ).exists():
                raise ValidationError(
                    {field_name: "The person must be an active organisation member."}
                )


class ScenarioSignpost(UUIDTimeStampedModel):
    """An explicit interpretation of how a signpost relates to one scenario."""

    class Relationship(models.TextChoices):
        SUPPORTS = "supports", "Supports"
        CONTRADICTS = "contradicts", "Contradicts"
        CONTEXTUAL = "contextual", "Contextual"

    signpost = models.ForeignKey(
        Signpost, on_delete=models.CASCADE, related_name="scenario_links"
    )
    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, related_name="signpost_links"
    )
    relationship = models.CharField(max_length=20, choices=Relationship.choices)
    rationale = models.TextField()
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="linked_scenario_signposts",
    )

    class Meta:
        ordering = ["scenario__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["signpost", "scenario"], name="unique_signpost_scenario_link"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if self.scenario_id and self.scenario.scenario_set_id != self.signpost.scenario_set_id:
            raise ValidationError(
                {"scenario": "Choose a scenario from the signpost's scenario set."}
            )
        if not self.rationale:
            raise ValidationError({"rationale": "Explain this signpost relationship."})


class SignpostObservation(UUIDTimeStampedModel):
    """A dated observation against an adaptive signpost."""

    class Assessment(models.TextChoices):
        NO_CHANGE = "no_change", "No meaningful change"
        WEAK = "weak", "Weak movement"
        MODERATE = "moderate", "Moderate movement"
        STRONG = "strong", "Strong movement"
        CONTRADICTORY = "contradictory", "Contradictory evidence"

    signpost = models.ForeignKey(
        Signpost, on_delete=models.CASCADE, related_name="observations"
    )
    observed_on = models.DateField()
    value = models.CharField(max_length=500)
    assessment = models.CharField(max_length=20, choices=Assessment.choices)
    evidence = models.TextField()
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        related_name="signpost_observations",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_signpost_observations",
    )

    class Meta:
        ordering = ["-observed_on", "-created_at"]

    def clean(self) -> None:
        super().clean()
        self.value = self.value.strip()
        self.evidence = self.evidence.strip()
        if not self.value:
            raise ValidationError({"value": "Record the observed value or condition."})
        if not self.evidence:
            raise ValidationError({"evidence": "Explain the evidence behind this observation."})
        if self.source_id:
            organisation_id = self.signpost.scenario_set.canvas.organisation_id
            if self.source.organisation_id != organisation_id:
                raise ValidationError(
                    {"source": "The source must share the signpost organisation."}
                )


class ScenarioImplicationLink(UUIDTimeStampedModel):
    """A traceable explanation of how one implication changes in one scenario."""

    class Effect(models.TextChoices):
        AMPLIFIES = "amplifies", "Amplifies"
        REDUCES = "reduces", "Reduces"
        CHANGES = "changes", "Changes"
        TRIGGERS = "triggers", "Triggers"

    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, related_name="implication_links"
    )
    implication = models.ForeignKey(
        StrategicImplication,
        on_delete=models.CASCADE,
        related_name="scenario_links",
    )
    effect = models.CharField(max_length=20, choices=Effect.choices)
    rationale = models.TextField()
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="linked_scenario_implications",
    )

    class Meta:
        ordering = ["implication__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["scenario", "implication"],
                name="unique_implication_per_scenario",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if self.implication_id:
            canvas_id = self.scenario.scenario_set.canvas_id
            if self.implication.canvas_id != canvas_id:
                raise ValidationError(
                    {"implication": "Choose an implication from the scenario canvas."}
                )
        if not self.rationale:
            raise ValidationError({"rationale": "Explain the scenario-specific effect."})
