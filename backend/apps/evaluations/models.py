"""Collective evaluation, minority reporting, and constrained prioritisation records."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class EvaluationExercise(UUIDTimeStampedModel):
    """Governed evaluation of the active options within one decision."""

    class Method(models.TextChoices):
        SCORECARD = "scorecard", "Multi-criteria scorecard"
        APPROVAL = "approval", "Approval voting"
        CONSENT = "consent", "Consent and objections"
        DELPHI = "delphi", "Delphi evaluation"
        RANKED_CHOICE = "ranked_choice", "Ranked-choice (instant runoff)"
        FORECASTING = "forecasting", "Calibrated forecasting"
        QUADRATIC = "quadratic", "Quadratic voting"
        LIQUID_DEMOCRACY = "liquid_democracy", "Liquid democracy"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    class Anonymity(models.TextChoices):
        ATTRIBUTED = "attributed", "Attributable"
        PEER_ANONYMOUS = "peer_anonymous", "Anonymous to peers"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="evaluation_exercises"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="evaluation_exercises"
    )
    title = models.CharField(max_length=240)
    purpose = models.TextField(blank=True)
    method = models.CharField(max_length=24, choices=Method.choices, default=Method.SCORECARD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    anonymity = models.CharField(
        max_length=24, choices=Anonymity.choices, default=Anonymity.ATTRIBUTED
    )
    blind_results_until_close = models.BooleanField(default=True)
    blind_applicant_identity = models.BooleanField(
        default=False,
        help_text="Hide option titles/descriptions from reviewers during scoring, showing 'Application A/B/…' instead.",
    )
    quorum_count = models.PositiveIntegerField(default=1)
    approval_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    objection_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    voice_credit_budget = models.PositiveIntegerField(
        default=100,
        help_text="Quadratic voting only: credits each participant may spend across their ballot.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_evaluation_exercises",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_evaluation_exercises",
    )

    class Meta:
        ordering = ["-updated_at", "title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quorum_count__gte=1), name="evaluation_quorum_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(approval_threshold__gte=0, approval_threshold__lte=100),
                name="evaluation_approval_threshold_range",
            ),
            models.CheckConstraint(
                condition=models.Q(objection_threshold__gte=0, objection_threshold__lte=100),
                name="evaluation_objection_threshold_range",
            ),
            models.CheckConstraint(
                condition=models.Q(voice_credit_budget__gte=1),
                name="evaluation_voice_credit_budget_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "status", "-updated_at"], name="evaluation_org_status_idx"
            ),
            models.Index(fields=["decision", "status"], name="evaluation_decision_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.purpose = self.purpose.strip()
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The exercise must share the decision organisation."}
            )


class EvaluationCriterion(UUIDTimeStampedModel):
    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="evaluation_criteria"
    )
    exercise = models.ForeignKey(
        EvaluationExercise, on_delete=models.CASCADE, related_name="criteria"
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    scale_min = models.PositiveSmallIntegerField(default=1)
    scale_max = models.PositiveSmallIntegerField(default=5)
    higher_is_better = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise", "title"], name="unique_evaluation_criterion_title"
            ),
            models.CheckConstraint(
                condition=models.Q(weight__gt=0), name="evaluation_criterion_weight_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(scale_max__gt=models.F("scale_min")),
                name="evaluation_criterion_scale_ordered",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        if (
            self.exercise_id
            and self.organisation_id
            and self.exercise.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The criterion must share the exercise organisation."}
            )


class EvaluationRound(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="evaluation_rounds"
    )
    exercise = models.ForeignKey(
        EvaluationExercise, on_delete=models.CASCADE, related_name="rounds"
    )
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    feedback_summary = models.TextField(blank=True)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="opened_evaluation_rounds",
        null=True,
        blank=True,
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="closed_evaluation_rounds",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["number", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise", "number"], name="unique_evaluation_round_number"
            ),
            models.UniqueConstraint(
                fields=["exercise"],
                condition=models.Q(status="open"),
                name="one_open_round_per_exercise",
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1), name="evaluation_round_number_positive"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.feedback_summary = self.feedback_summary.strip()
        if (
            self.exercise_id
            and self.organisation_id
            and self.exercise.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The round must share the exercise organisation."}
            )


class EvaluationSubmission(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="evaluation_submissions",
    )
    round = models.ForeignKey(EvaluationRound, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evaluation_submissions"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    confidence = models.PositiveSmallIntegerField(default=3)
    overall_rationale = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["round", "submitted_by"], name="one_submission_per_round_user"
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__gte=1, confidence__lte=5),
                name="evaluation_submission_confidence_range",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.overall_rationale = self.overall_rationale.strip()
        if (
            self.round_id
            and self.organisation_id
            and self.round.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The submission must share the round organisation."}
            )
        if self.status == self.Status.SUBMITTED and self.submitted_at is None:
            self.submitted_at = timezone.now()


class EvaluationResponse(UUIDTimeStampedModel):
    class Vote(models.TextChoices):
        APPROVE = "approve", "Approve"
        CONSENT = "consent", "Consent"
        CONCERN = "concern", "Concern"
        OBJECT = "object", "Object"
        ABSTAIN = "abstain", "Abstain"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="evaluation_responses"
    )
    submission = models.ForeignKey(
        EvaluationSubmission, on_delete=models.CASCADE, related_name="responses"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.CASCADE,
        related_name="evaluation_responses",
    )
    criterion = models.ForeignKey(
        EvaluationCriterion,
        on_delete=models.CASCADE,
        related_name="responses",
        null=True,
        blank=True,
    )
    score = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    vote = models.CharField(max_length=20, choices=Vote.choices, blank=True)
    rank = models.PositiveSmallIntegerField(null=True, blank=True)
    quadratic_votes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Signed vote count for a quadratic-voting ballot; positive supports, negative opposes.",
    )
    rationale = models.TextField(blank=True)

    class Meta:
        ordering = ["option__title", "criterion__order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "option", "criterion"],
                condition=models.Q(criterion__isnull=False),
                name="unique_scored_response",
            ),
            models.UniqueConstraint(
                fields=["submission", "option"],
                condition=models.Q(criterion__isnull=True),
                name="unique_ballot_response",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        exercise = self.submission.round.exercise if self.submission_id else None
        if exercise and self.option.decision_id != exercise.decision_id:
            raise ValidationError(
                {"option": "Select an active option from the evaluated decision."}
            )
        if self.criterion_id and self.criterion.exercise_id != exercise.id:
            raise ValidationError({"criterion": "The criterion must belong to this exercise."})
        is_ranked_choice = (
            exercise is not None and exercise.method == EvaluationExercise.Method.RANKED_CHOICE
        )
        is_quadratic = (
            exercise is not None and exercise.method == EvaluationExercise.Method.QUADRATIC
        )
        if self.criterion_id:
            if self.score is None:
                raise ValidationError({"score": "A criterion response requires a score."})
            if self.score < self.criterion.scale_min or self.score > self.criterion.scale_max:
                raise ValidationError({"score": "The score is outside the criterion scale."})
        elif is_ranked_choice:
            if self.rank is None:
                raise ValidationError({"rank": "A ranked-choice response requires a rank."})
            if self.vote:
                raise ValidationError({"vote": "Ranked-choice responses do not use a vote."})
        elif is_quadratic:
            if not self.quadratic_votes:
                raise ValidationError(
                    {"quadratic_votes": "A quadratic ballot response requires a non-zero vote count."}
                )
            if self.vote:
                raise ValidationError({"vote": "Quadratic ballot responses do not use a vote."})
        elif not self.vote:
            raise ValidationError({"vote": "A ballot response requires a vote."})
        if not is_ranked_choice and self.rank is not None:
            raise ValidationError({"rank": "Rank is only meaningful for a ranked-choice exercise."})
        if not is_quadratic and self.quadratic_votes is not None:
            raise ValidationError(
                {"quadratic_votes": "Vote counts are only meaningful for a quadratic-voting exercise."}
            )


class MinorityReport(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="minority_reports"
    )
    exercise = models.ForeignKey(
        EvaluationExercise, on_delete=models.CASCADE, related_name="minority_reports"
    )
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.SET_NULL,
        related_name="minority_reports",
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="minority_reports"
    )
    title = models.CharField(max_length=200)
    analysis = models.TextField()
    recommendation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-published_at", "id"]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.analysis = self.analysis.strip()
        self.recommendation = self.recommendation.strip()
        if (
            self.exercise_id
            and self.organisation_id
            and self.exercise.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The report must share the exercise organisation."}
            )
        if self.round_id and self.round.exercise_id != self.exercise_id:
            raise ValidationError({"round": "The round must belong to this exercise."})


class PrioritisationPortfolio(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open for assessment"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="prioritisation_portfolios",
    )
    title = models.CharField(max_length=240)
    purpose = models.TextField(blank=True)
    budget_limit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    capacity_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    anonymity = models.CharField(
        max_length=24,
        choices=EvaluationExercise.Anonymity.choices,
        default=EvaluationExercise.Anonymity.ATTRIBUTED,
    )
    blind_results_until_close = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_prioritisation_portfolios",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_prioritisation_portfolios",
    )

    class Meta:
        ordering = ["-updated_at", "title", "id"]
        indexes = [
            models.Index(
                fields=["organisation", "status", "-updated_at"], name="priority_portfolio_org_idx"
            )
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.purpose = self.purpose.strip()
        for field in ("budget_limit", "capacity_limit"):
            value = getattr(self, field)
            if value is not None and value < 0:
                raise ValidationError({field: "Use a non-negative constraint."})


class PortfolioCriterion(UUIDTimeStampedModel):
    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="portfolio_criteria"
    )
    portfolio = models.ForeignKey(
        PrioritisationPortfolio, on_delete=models.CASCADE, related_name="criteria"
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    higher_is_better = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "title"], name="unique_portfolio_criterion_title"
            ),
            models.CheckConstraint(
                condition=models.Q(weight__gt=0), name="portfolio_criterion_weight_positive"
            ),
        ]


class PortfolioCandidate(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        WITHDRAWN = "withdrawn", "Withdrawn"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="portfolio_candidates"
    )
    portfolio = models.ForeignKey(
        PrioritisationPortfolio, on_delete=models.CASCADE, related_name="candidates"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="portfolio_candidates"
    )
    budget_required = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    capacity_required = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mandatory = models.BooleanField(default=False)
    rationale = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="added_portfolio_candidates",
    )

    class Meta:
        ordering = ["-mandatory", "decision__title", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "decision"], name="unique_decision_per_priority_portfolio"
            ),
            models.CheckConstraint(
                condition=models.Q(budget_required__gte=0), name="candidate_budget_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(capacity_required__gte=0), name="candidate_capacity_nonnegative"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if (
            self.portfolio_id
            and self.organisation_id
            and self.portfolio.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The candidate must share the portfolio organisation."}
            )
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError({"decision": "Select a decision from this organisation."})


class PortfolioAssessment(UUIDTimeStampedModel):
    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="portfolio_assessments"
    )
    candidate = models.ForeignKey(
        PortfolioCandidate, on_delete=models.CASCADE, related_name="assessments"
    )
    criterion = models.ForeignKey(
        PortfolioCriterion, on_delete=models.CASCADE, related_name="assessments"
    )
    assessor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="portfolio_assessments"
    )
    score = models.DecimalField(max_digits=6, decimal_places=3)
    confidence = models.PositiveSmallIntegerField(default=3)
    rationale = models.TextField(blank=True)

    class Meta:
        ordering = ["candidate__decision__title", "criterion__order", "assessor__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "criterion", "assessor"], name="unique_portfolio_assessment"
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=0, score__lte=100), name="portfolio_score_range"
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__gte=1, confidence__lte=5),
                name="portfolio_confidence_range",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if (
            self.candidate_id
            and self.criterion_id
            and self.candidate.portfolio_id != self.criterion.portfolio_id
        ):
            raise ValidationError(
                {"criterion": "The criterion must belong to the candidate portfolio."}
            )


class PortfolioSelection(UUIDTimeStampedModel):
    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="portfolio_selections"
    )
    candidate = models.OneToOneField(
        PortfolioCandidate, on_delete=models.CASCADE, related_name="selection"
    )
    selected = models.BooleanField(default=False)
    priority_order = models.PositiveSmallIntegerField(null=True, blank=True)
    approved_budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    approved_capacity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rationale = models.TextField(blank=True)
    selected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="portfolio_selections"
    )
    selected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-selected", "priority_order", "candidate__decision__title"]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if (
            self.candidate_id
            and self.organisation_id
            and self.candidate.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The selection must share the candidate organisation."}
            )


class ForecastQuestion(UUIDTimeStampedModel):
    """A yes/no question forecasters assign a probability to, within a forecasting exercise."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="forecast_questions"
    )
    exercise = models.ForeignKey(
        EvaluationExercise, on_delete=models.CASCADE, related_name="forecast_questions"
    )
    question_text = models.CharField(max_length=300)
    resolution_criteria = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    outcome = models.BooleanField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resolved_forecast_questions",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["exercise", "status"], name="forecast_question_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.question_text = self.question_text.strip()
        self.resolution_criteria = self.resolution_criteria.strip()
        if (
            self.exercise_id
            and self.organisation_id
            and self.exercise.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The question must share the exercise organisation."}
            )
        if self.exercise_id and self.exercise.method != EvaluationExercise.Method.FORECASTING:
            raise ValidationError(
                {
                    "exercise": "Forecast questions may only be added to a calibrated-forecasting exercise."
                }
            )
        if self.status == self.Status.RESOLVED and (
            self.outcome is None or self.resolved_at is None or self.resolved_by_id is None
        ):
            raise ValidationError(
                "A resolved question requires an outcome, a resolution time, and who resolved it."
            )
        if self.status == self.Status.OPEN and (
            self.outcome is not None or self.resolved_at is not None or self.resolved_by_id is not None
        ):
            raise ValidationError("An open question cannot carry resolution metadata.")


class Forecast(UUIDTimeStampedModel):
    """One participant's current probability estimate for a forecast question."""

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="forecasts"
    )
    question = models.ForeignKey(
        ForecastQuestion, on_delete=models.CASCADE, related_name="forecasts"
    )
    forecaster = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="forecasts"
    )
    probability = models.DecimalField(max_digits=5, decimal_places=2)
    brier_score = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "forecaster"], name="one_forecast_per_question_per_forecaster"
            ),
            models.CheckConstraint(
                condition=models.Q(probability__gte=0, probability__lte=100),
                name="forecast_probability_range",
            ),
        ]
        indexes = [
            models.Index(fields=["organisation", "forecaster"], name="forecast_org_forecaster_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        if (
            self.question_id
            and self.organisation_id
            and self.question.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The forecast must share the question organisation."}
            )


class LiquidVote(UUIDTimeStampedModel):
    """A participant's standing choice in a liquid-democracy exercise: a direct vote or a delegation.

    Casting a new direct vote or delegation always replaces whichever of the
    two this voter previously had - there is exactly one row per (exercise,
    voter), which is what lets a direct vote silently override a standing
    delegation, per the mechanism's own rule.
    """

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="liquid_votes"
    )
    exercise = models.ForeignKey(EvaluationExercise, on_delete=models.CASCADE, related_name="liquid_votes")
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="liquid_votes"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.CASCADE,
        related_name="liquid_votes",
        null=True,
        blank=True,
    )
    delegate_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="liquid_delegations_received",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-updated_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["exercise", "voter"], name="unique_liquid_vote_per_exercise_voter"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(option__isnull=False, delegate_to__isnull=True)
                    | models.Q(option__isnull=True, delegate_to__isnull=False)
                ),
                name="liquid_vote_exactly_one_choice",
            ),
        ]
        indexes = [
            models.Index(fields=["exercise", "delegate_to"], name="liquid_vote_delegate_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        if (
            self.exercise_id
            and self.organisation_id
            and self.exercise.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The vote must share the exercise organisation."}
            )
        if self.exercise_id and self.exercise.method != EvaluationExercise.Method.LIQUID_DEMOCRACY:
            raise ValidationError(
                {"exercise": "Liquid votes may only be cast in a liquid-democracy exercise."}
            )
        if self.option_id and self.delegate_to_id:
            raise ValidationError("Choose either a direct vote or a delegation, not both.")
        if not self.option_id and not self.delegate_to_id:
            raise ValidationError("Choose either a direct vote or a delegation.")
        if self.delegate_to_id and self.voter_id and self.delegate_to_id == self.voter_id:
            raise ValidationError({"delegate_to": "You cannot delegate to yourself."})
        if (
            self.option_id
            and self.exercise_id
            and self.option.decision_id != self.exercise.decision_id
        ):
            raise ValidationError(
                {"option": "Select an active option from the evaluated decision."}
            )
