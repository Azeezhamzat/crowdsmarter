from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.decision_options.services import create_option
from apps.evaluations.models import EvaluationExercise, Forecast, ForecastQuestion, LiquidVote
from apps.evaluations.services import create_exercise


@pytest.mark.django_db
def test_forecast_question_requires_a_forecasting_exercise(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Scorecard",
        purpose="p",
        method="scorecard",
        quorum_count=1,
    )
    question = ForecastQuestion(
        organisation=exercise.organisation, exercise=exercise, question_text="Will X happen?"
    )
    with pytest.raises(ValidationError):
        question.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_forecast_question_resolved_requires_outcome_metadata(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    question = ForecastQuestion(
        organisation=exercise.organisation,
        exercise=exercise,
        question_text="Will X happen?",
        status=ForecastQuestion.Status.RESOLVED,
    )
    with pytest.raises(ValidationError):
        question.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_forecast_question_open_cannot_carry_resolution_metadata(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    question = ForecastQuestion(
        organisation=exercise.organisation,
        exercise=exercise,
        question_text="Will X happen?",
        status=ForecastQuestion.Status.OPEN,
        outcome=True,
        resolved_at=timezone.now(),
        resolved_by=owner,
    )
    with pytest.raises(ValidationError):
        question.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_forecast_probability_out_of_range_is_rejected(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    question = ForecastQuestion.objects.create(
        organisation=exercise.organisation, exercise=exercise, question_text="Will X happen?"
    )
    forecast = Forecast(
        organisation=exercise.organisation,
        question=question,
        forecaster=owner,
        probability=Decimal("150"),
    )
    with pytest.raises(ValidationError):
        forecast.full_clean(validate_unique=False)


@pytest.mark.django_db
def test_forecast_requires_matching_question_organisation(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    other_organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Forecasting",
        purpose="p",
        method="forecasting",
        quorum_count=1,
    )
    question = ForecastQuestion.objects.create(
        organisation=exercise.organisation, exercise=exercise, question_text="Will X happen?"
    )
    forecast = Forecast(
        organisation=other_organisation,
        question=question,
        forecaster=owner,
        probability=Decimal("50"),
    )
    with pytest.raises(ValidationError):
        forecast.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_evaluation_exercise_voice_credit_budget_must_be_positive(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = EvaluationExercise(
        organisation=organisation,
        decision=decision,
        title="Quadratic voting",
        purpose="p",
        method=EvaluationExercise.Method.QUADRATIC,
        owner=owner,
        created_by=owner,
        voice_credit_budget=0,
    )
    with pytest.raises(ValidationError):
        exercise.full_clean(validate_unique=False)


@pytest.mark.django_db
def test_liquid_vote_requires_a_liquid_democracy_exercise(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Scorecard",
        purpose="p",
        method="scorecard",
        quorum_count=1,
    )
    vote = LiquidVote(
        organisation=exercise.organisation, exercise=exercise, voter=owner, option=option
    )
    with pytest.raises(ValidationError):
        vote.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_liquid_vote_requires_exactly_one_of_option_or_delegate(
    organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    other = user_factory(email="other@example.com")
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    option = create_option(actor=owner, decision=decision, title="Option A", description="d")
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Liquid democracy",
        purpose="p",
        method="liquid_democracy",
        quorum_count=1,
    )
    neither = LiquidVote(organisation=exercise.organisation, exercise=exercise, voter=owner)
    with pytest.raises(ValidationError):
        neither.full_clean(validate_unique=False, validate_constraints=False)

    both = LiquidVote(
        organisation=exercise.organisation,
        exercise=exercise,
        voter=owner,
        option=option,
        delegate_to=other,
    )
    with pytest.raises(ValidationError):
        both.full_clean(validate_unique=False, validate_constraints=False)


@pytest.mark.django_db
def test_liquid_vote_rejects_self_delegation(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    exercise = create_exercise(
        actor=owner,
        decision=decision,
        owner_id=owner.id,
        title="Liquid democracy",
        purpose="p",
        method="liquid_democracy",
        quorum_count=1,
    )
    vote = LiquidVote(
        organisation=exercise.organisation, exercise=exercise, voter=owner, delegate_to=owner
    )
    with pytest.raises(ValidationError):
        vote.full_clean(validate_unique=False, validate_constraints=False)
