"""REST representations for collective evaluation and constrained prioritisation."""

from decimal import Decimal

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import (
    EvaluationCriterion,
    EvaluationExercise,
    EvaluationResponse,
    EvaluationRound,
    EvaluationSubmission,
    Forecast,
    ForecastQuestion,
    LiquidVote,
    MinorityReport,
    OpinionStatement,
    OpinionVote,
    PortfolioAssessment,
    PortfolioCandidate,
    PortfolioCriterion,
    PortfolioSelection,
    PrioritisationPortfolio,
)
from .policies import (
    can_assess_portfolio,
    can_manage_exercise,
    can_manage_portfolio,
    can_submit_evaluation,
)
from .services import evaluation_results, portfolio_recommendation


class EvaluationCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationCriterion
        fields = [
            "id",
            "exercise_id",
            "title",
            "description",
            "weight",
            "scale_min",
            "scale_max",
            "higher_is_better",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EvaluationCriterionWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, max_length=8000)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.01"))
    scale_min = serializers.IntegerField(required=False, default=1, min_value=0, max_value=99)
    scale_max = serializers.IntegerField(required=False, default=5, min_value=1, max_value=100)
    higher_is_better = serializers.BooleanField(required=False, default=True)
    order = serializers.IntegerField(required=False, default=0, min_value=0, max_value=999)

    def validate(self, attrs):
        if attrs["scale_max"] <= attrs["scale_min"]:
            raise serializers.ValidationError(
                {"scale_max": "The maximum must be greater than the minimum."}
            )
        return attrs


class EvaluationResponseSerializer(serializers.ModelSerializer):
    option_title = serializers.CharField(source="option.title", read_only=True)
    criterion_title = serializers.CharField(
        source="criterion.title", read_only=True, allow_null=True
    )

    class Meta:
        model = EvaluationResponse
        fields = [
            "id",
            "option_id",
            "option_title",
            "criterion_id",
            "criterion_title",
            "score",
            "vote",
            "rank",
            "quadratic_votes",
            "rationale",
            "created_at",
        ]
        read_only_fields = fields


class EvaluationSubmissionSerializer(serializers.ModelSerializer):
    respondent = serializers.SerializerMethodField()
    responses = EvaluationResponseSerializer(many=True, read_only=True)

    class Meta:
        model = EvaluationSubmission
        fields = [
            "id",
            "round_id",
            "respondent",
            "status",
            "confidence",
            "overall_rationale",
            "submitted_at",
            "responses",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_respondent(self, obj):
        exercise = obj.round.exercise
        request = self.context.get("request")
        if exercise.anonymity == EvaluationExercise.Anonymity.PEER_ANONYMOUS and (
            request is None or request.user.id != obj.submitted_by_id
        ):
            ids = list(
                obj.round.submissions.order_by("created_at", "id").values_list("id", flat=True)
            )
            return {"anonymous": True, "label": f"Contributor {ids.index(obj.id) + 1}"}
        return {"anonymous": False, "user": DecisionUserSerializer(obj.submitted_by).data}


class EvaluationRoundSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()
    result_summary = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationRound
        fields = [
            "id",
            "exercise_id",
            "number",
            "title",
            "status",
            "feedback_summary",
            "opens_at",
            "closes_at",
            "submissions",
            "result_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_submissions(self, obj):
        exercise = obj.exercise
        if exercise.blind_results_until_close and obj.status != EvaluationRound.Status.CLOSED:
            request = self.context.get("request")
            mine = (
                obj.submissions.filter(submitted_by=request.user)
                if request
                else obj.submissions.none()
            )
            return EvaluationSubmissionSerializer(mine, many=True, context=self.context).data
        return EvaluationSubmissionSerializer(
            obj.submissions.all(), many=True, context=self.context
        ).data

    def get_result_summary(self, obj):
        request = self.context.get("request")
        return evaluation_results(round=obj, viewer=request.user if request else None)


class MinorityReportSerializer(serializers.ModelSerializer):
    author = DecisionUserSerializer(read_only=True)

    class Meta:
        model = MinorityReport
        fields = [
            "id",
            "exercise_id",
            "round_id",
            "author",
            "title",
            "analysis",
            "recommendation",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ForecastSerializer(serializers.ModelSerializer):
    respondent = serializers.SerializerMethodField()

    class Meta:
        model = Forecast
        fields = [
            "id",
            "question_id",
            "respondent",
            "probability",
            "brier_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_respondent(self, obj):
        exercise = obj.question.exercise
        request = self.context.get("request")
        if exercise.anonymity == EvaluationExercise.Anonymity.PEER_ANONYMOUS and (
            request is None or request.user.id != obj.forecaster_id
        ):
            ids = list(
                obj.question.forecasts.order_by("created_at", "id").values_list("id", flat=True)
            )
            return {"anonymous": True, "label": f"Forecaster {ids.index(obj.id) + 1}"}
        return {"anonymous": False, "user": DecisionUserSerializer(obj.forecaster).data}


class ForecastQuestionSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    resolved_by = DecisionUserSerializer(read_only=True)
    forecasts = serializers.SerializerMethodField()

    class Meta:
        model = ForecastQuestion
        fields = [
            "id",
            "exercise_id",
            "question_text",
            "resolution_criteria",
            "status",
            "status_label",
            "outcome",
            "resolved_at",
            "resolved_by",
            "forecasts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_forecasts(self, obj):
        exercise = obj.exercise
        if exercise.blind_results_until_close and obj.status != ForecastQuestion.Status.RESOLVED:
            request = self.context.get("request")
            mine = (
                obj.forecasts.filter(forecaster=request.user) if request else obj.forecasts.none()
            )
            return ForecastSerializer(mine, many=True, context=self.context).data
        return ForecastSerializer(obj.forecasts.all(), many=True, context=self.context).data


class ForecastQuestionWriteSerializer(StrictSerializer):
    question_text = serializers.CharField(max_length=300)
    resolution_criteria = serializers.CharField(required=False, allow_blank=True, max_length=8000)


class ForecastQuestionResolveSerializer(StrictSerializer):
    outcome = serializers.BooleanField()


class ForecastWriteSerializer(StrictSerializer):
    probability = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100
    )


class OpinionStatementSerializer(serializers.ModelSerializer):
    author = DecisionUserSerializer(read_only=True)
    agree_count = serializers.SerializerMethodField()
    disagree_count = serializers.SerializerMethodField()

    class Meta:
        model = OpinionStatement
        fields = [
            "id",
            "exercise_id",
            "author",
            "text",
            "agree_count",
            "disagree_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_agree_count(self, obj):
        return sum(1 for vote in obj.votes.all() if vote.choice == OpinionVote.Choice.AGREE)

    def get_disagree_count(self, obj):
        return sum(1 for vote in obj.votes.all() if vote.choice == OpinionVote.Choice.DISAGREE)


class OpinionStatementWriteSerializer(StrictSerializer):
    text = serializers.CharField(max_length=500)


class OpinionVoteSerializer(serializers.ModelSerializer):
    voter = DecisionUserSerializer(read_only=True)

    class Meta:
        model = OpinionVote
        fields = ["id", "statement_id", "voter", "choice", "created_at", "updated_at"]
        read_only_fields = fields


class OpinionVoteWriteSerializer(StrictSerializer):
    choice = serializers.ChoiceField(choices=OpinionVote.Choice.choices)


class EvaluationExerciseSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    method_label = serializers.CharField(source="get_method_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    criteria = EvaluationCriterionSerializer(many=True, read_only=True)
    rounds = EvaluationRoundSerializer(many=True, read_only=True)
    minority_reports = MinorityReportSerializer(many=True, read_only=True)
    forecast_questions = ForecastQuestionSerializer(many=True, read_only=True)
    opinion_statements = OpinionStatementSerializer(many=True, read_only=True)
    can_manage = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationExercise
        fields = [
            "id",
            "organisation_id",
            "decision_id",
            "title",
            "purpose",
            "method",
            "method_label",
            "status",
            "status_label",
            "anonymity",
            "blind_results_until_close",
            "blind_applicant_identity",
            "quorum_count",
            "approval_threshold",
            "objection_threshold",
            "voice_credit_budget",
            "owner",
            "created_by",
            "criteria",
            "rounds",
            "minority_reports",
            "forecast_questions",
            "opinion_statements",
            "can_manage",
            "can_submit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_manage(self, obj):
        request = self.context.get("request")
        return bool(request and can_manage_exercise(actor=request.user, exercise=obj))

    def get_can_submit(self, obj):
        request = self.context.get("request")
        return bool(request and can_submit_evaluation(actor=request.user, exercise=obj))


class EvaluationExerciseWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240)
    purpose = serializers.CharField(required=False, allow_blank=True, max_length=12000)
    method = serializers.ChoiceField(choices=EvaluationExercise.Method.choices)
    anonymity = serializers.ChoiceField(
        choices=EvaluationExercise.Anonymity.choices,
        required=False,
        default=EvaluationExercise.Anonymity.ATTRIBUTED,
    )
    blind_results_until_close = serializers.BooleanField(required=False, default=True)
    blind_applicant_identity = serializers.BooleanField(required=False, default=False)
    quorum_count = serializers.IntegerField(required=False, default=1, min_value=1, max_value=10000)
    approval_threshold = serializers.DecimalField(
        required=False,
        default=Decimal("60"),
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
    )
    objection_threshold = serializers.DecimalField(
        required=False,
        default=Decimal("20"),
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
    )
    voice_credit_budget = serializers.IntegerField(
        required=False, default=100, min_value=1, max_value=1000000
    )
    owner_id = serializers.UUIDField()


class EvaluationExercisePatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, required=False)
    purpose = serializers.CharField(required=False, allow_blank=True, max_length=12000)
    status = serializers.ChoiceField(choices=EvaluationExercise.Status.choices, required=False)
    anonymity = serializers.ChoiceField(
        choices=EvaluationExercise.Anonymity.choices, required=False
    )
    blind_results_until_close = serializers.BooleanField(required=False)
    blind_applicant_identity = serializers.BooleanField(required=False)
    quorum_count = serializers.IntegerField(required=False, min_value=1, max_value=10000)
    approval_threshold = serializers.DecimalField(
        required=False, max_digits=5, decimal_places=2, min_value=0, max_value=100
    )
    objection_threshold = serializers.DecimalField(
        required=False, max_digits=5, decimal_places=2, min_value=0, max_value=100
    )
    voice_credit_budget = serializers.IntegerField(required=False, min_value=1, max_value=1000000)
    owner_id = serializers.UUIDField(required=False)


class EvaluationRoundWriteSerializer(StrictSerializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)


class EvaluationRoundTransitionSerializer(StrictSerializer):
    status = serializers.ChoiceField(
        choices=[EvaluationRound.Status.OPEN, EvaluationRound.Status.CLOSED]
    )
    feedback_summary = serializers.CharField(required=False, allow_blank=True, max_length=16000)


class EvaluationResponseWriteSerializer(StrictSerializer):
    option_id = serializers.UUIDField()
    criterion_id = serializers.UUIDField(required=False, allow_null=True)
    score = serializers.DecimalField(
        required=False, allow_null=True, max_digits=8, decimal_places=3
    )
    vote = serializers.ChoiceField(
        required=False, allow_blank=True, choices=EvaluationResponse.Vote.choices
    )
    rank = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=9999)
    quadratic_votes = serializers.IntegerField(
        required=False, allow_null=True, min_value=-1000, max_value=1000
    )
    rationale = serializers.CharField(required=False, allow_blank=True, max_length=8000)


class EvaluationScoringOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    blinded = serializers.BooleanField()


class EvaluationSubmissionWriteSerializer(StrictSerializer):
    confidence = serializers.IntegerField(min_value=1, max_value=5)
    overall_rationale = serializers.CharField(required=False, allow_blank=True, max_length=16000)
    responses = EvaluationResponseWriteSerializer(many=True)
    submit = serializers.BooleanField(required=False, default=True)


class MinorityReportWriteSerializer(StrictSerializer):
    round_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=200)
    analysis = serializers.CharField(max_length=30000)
    recommendation = serializers.CharField(required=False, allow_blank=True, max_length=16000)


class PortfolioCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioCriterion
        fields = [
            "id",
            "portfolio_id",
            "title",
            "description",
            "weight",
            "higher_is_better",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PortfolioCriterionWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True, max_length=8000)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.01"))
    higher_is_better = serializers.BooleanField(required=False, default=True)
    order = serializers.IntegerField(required=False, default=0, min_value=0, max_value=999)


class PortfolioAssessmentSerializer(serializers.ModelSerializer):
    respondent = serializers.SerializerMethodField()
    criterion_title = serializers.CharField(source="criterion.title", read_only=True)

    class Meta:
        model = PortfolioAssessment
        fields = [
            "id",
            "candidate_id",
            "criterion_id",
            "criterion_title",
            "respondent",
            "score",
            "confidence",
            "rationale",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_respondent(self, obj):
        portfolio = obj.candidate.portfolio
        request = self.context.get("request")
        if portfolio.anonymity == EvaluationExercise.Anonymity.PEER_ANONYMOUS and (
            request is None or request.user.id != obj.assessor_id
        ):
            assessor_ids = list(
                PortfolioAssessment.objects.filter(candidate__portfolio=portfolio)
                .order_by("created_at", "id")
                .values_list("assessor_id", flat=True)
            )
            stable_ids = list(dict.fromkeys(assessor_ids))
            return {"anonymous": True, "label": f"Assessor {stable_ids.index(obj.assessor_id) + 1}"}
        return {"anonymous": False, "user": DecisionUserSerializer(obj.assessor).data}


class PortfolioSelectionSerializer(serializers.ModelSerializer):
    selected_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = PortfolioSelection
        fields = [
            "id",
            "candidate_id",
            "selected",
            "priority_order",
            "approved_budget",
            "approved_capacity",
            "rationale",
            "selected_by",
            "selected_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PortfolioCandidateSerializer(serializers.ModelSerializer):
    decision_title = serializers.CharField(source="decision.title", read_only=True)
    decision_status = serializers.CharField(source="decision.status", read_only=True)
    assessments = serializers.SerializerMethodField()
    selection = PortfolioSelectionSerializer(read_only=True)

    class Meta:
        model = PortfolioCandidate
        fields = [
            "id",
            "portfolio_id",
            "decision_id",
            "decision_title",
            "decision_status",
            "budget_required",
            "capacity_required",
            "mandatory",
            "rationale",
            "status",
            "assessments",
            "selection",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_assessments(self, obj):
        portfolio = obj.portfolio
        items = obj.assessments.all()
        if (
            portfolio.blind_results_until_close
            and portfolio.status == PrioritisationPortfolio.Status.OPEN
        ):
            request = self.context.get("request")
            items = items.filter(assessor=request.user) if request else items.none()
        return PortfolioAssessmentSerializer(items, many=True, context=self.context).data


class PrioritisationPortfolioSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    criteria = PortfolioCriterionSerializer(many=True, read_only=True)
    candidates = PortfolioCandidateSerializer(many=True, read_only=True)
    recommendation = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    can_assess = serializers.SerializerMethodField()

    class Meta:
        model = PrioritisationPortfolio
        fields = [
            "id",
            "organisation_id",
            "title",
            "purpose",
            "budget_limit",
            "capacity_limit",
            "status",
            "anonymity",
            "blind_results_until_close",
            "owner",
            "created_by",
            "criteria",
            "candidates",
            "recommendation",
            "can_manage",
            "can_assess",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_recommendation(self, obj):
        return portfolio_recommendation(portfolio=obj)

    def get_can_manage(self, obj):
        request = self.context.get("request")
        return bool(request and can_manage_portfolio(actor=request.user, portfolio=obj))

    def get_can_assess(self, obj):
        request = self.context.get("request")
        return bool(request and can_assess_portfolio(actor=request.user, portfolio=obj))


class PrioritisationPortfolioWriteSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240)
    purpose = serializers.CharField(required=False, allow_blank=True, max_length=12000)
    budget_limit = serializers.DecimalField(
        required=False, allow_null=True, max_digits=14, decimal_places=2, min_value=0
    )
    capacity_limit = serializers.DecimalField(
        required=False, allow_null=True, max_digits=12, decimal_places=2, min_value=0
    )
    anonymity = serializers.ChoiceField(
        required=False,
        default=EvaluationExercise.Anonymity.ATTRIBUTED,
        choices=EvaluationExercise.Anonymity.choices,
    )
    blind_results_until_close = serializers.BooleanField(required=False, default=True)
    owner_id = serializers.UUIDField()


class PrioritisationPortfolioPatchSerializer(StrictSerializer):
    title = serializers.CharField(required=False, max_length=240)
    purpose = serializers.CharField(required=False, allow_blank=True, max_length=12000)
    budget_limit = serializers.DecimalField(
        required=False, allow_null=True, max_digits=14, decimal_places=2, min_value=0
    )
    capacity_limit = serializers.DecimalField(
        required=False, allow_null=True, max_digits=12, decimal_places=2, min_value=0
    )
    anonymity = serializers.ChoiceField(
        required=False, choices=EvaluationExercise.Anonymity.choices
    )
    blind_results_until_close = serializers.BooleanField(required=False)
    status = serializers.ChoiceField(required=False, choices=PrioritisationPortfolio.Status.choices)
    owner_id = serializers.UUIDField(required=False)


class PortfolioCandidateWriteSerializer(StrictSerializer):
    decision_id = serializers.UUIDField()
    budget_required = serializers.DecimalField(
        required=False, default=Decimal("0"), max_digits=14, decimal_places=2, min_value=0
    )
    capacity_required = serializers.DecimalField(
        required=False, default=Decimal("0"), max_digits=12, decimal_places=2, min_value=0
    )
    mandatory = serializers.BooleanField(required=False, default=False)
    rationale = serializers.CharField(required=False, allow_blank=True, max_length=8000)


class PortfolioAssessmentWriteSerializer(StrictSerializer):
    criterion_id = serializers.UUIDField()
    score = serializers.DecimalField(max_digits=6, decimal_places=3, min_value=0, max_value=100)
    confidence = serializers.IntegerField(required=False, default=3, min_value=1, max_value=5)
    rationale = serializers.CharField(required=False, allow_blank=True, max_length=8000)


class PortfolioSelectionWriteSerializer(StrictSerializer):
    selected = serializers.BooleanField()
    priority_order = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=999
    )
    approved_budget = serializers.DecimalField(
        required=False, allow_null=True, max_digits=14, decimal_places=2, min_value=0
    )
    approved_capacity = serializers.DecimalField(
        required=False, allow_null=True, max_digits=12, decimal_places=2, min_value=0
    )
    rationale = serializers.CharField(required=False, allow_blank=True, max_length=12000)


class LiquidVoteSerializer(serializers.ModelSerializer):
    voter = DecisionUserSerializer(read_only=True)
    option_title = serializers.CharField(source="option.title", read_only=True, allow_null=True)
    delegate_to = DecisionUserSerializer(read_only=True)

    class Meta:
        model = LiquidVote
        fields = [
            "id",
            "exercise_id",
            "voter",
            "option_id",
            "option_title",
            "delegate_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class LiquidVoteWriteSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    delegate_to_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if bool(attrs.get("option_id")) == bool(attrs.get("delegate_to_id")):
            raise serializers.ValidationError(
                "Provide exactly one of option_id (a direct vote) or delegate_to_id (a delegation)."
            )
        return attrs
