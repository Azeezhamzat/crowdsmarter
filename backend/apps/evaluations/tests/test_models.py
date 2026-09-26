from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.evaluations.models import Forecast, ForecastQuestion
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
