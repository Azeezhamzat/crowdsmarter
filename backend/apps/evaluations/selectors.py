"""Tenant-safe selectors for collective evaluation."""

from django.shortcuts import get_object_or_404

from apps.decisions.selectors import decision_for_user
from apps.organisations.models import Organisation

from .models import (
    EvaluationExercise,
    EvaluationRound,
    ForecastQuestion,
    PortfolioCandidate,
    PrioritisationPortfolio,
)


def exercises_for_decision(*, user, decision_id):
    decision = decision_for_user(user=user, decision_id=decision_id)
    return (
        EvaluationExercise.objects.filter(decision=decision)
        .select_related("decision", "organisation", "owner", "created_by")
        .prefetch_related(
            "criteria", "rounds", "forecast_questions__forecasts__forecaster", "forecast_questions__resolved_by"
        )
    )


def exercise_for_user(*, user, exercise_id):
    return get_object_or_404(
        EvaluationExercise.objects.select_related(
            "decision", "organisation", "owner", "created_by"
        ).filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=exercise_id,
    )


def exercise_workspace_for_user(*, user, exercise_id):
    return get_object_or_404(
        EvaluationExercise.objects.select_related("decision", "organisation", "owner", "created_by")
        .prefetch_related(
            "criteria",
            "rounds__submissions__submitted_by",
            "rounds__submissions__responses__option",
            "rounds__submissions__responses__criterion",
            "minority_reports__author",
            "forecast_questions__forecasts__forecaster",
            "forecast_questions__resolved_by",
        )
        .filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=exercise_id,
    )


def round_for_user(*, user, round_id):
    return get_object_or_404(
        EvaluationRound.objects.select_related(
            "exercise__decision", "exercise__organisation", "exercise__owner"
        ).filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=round_id,
    )


def forecast_question_for_user(*, user, question_id):
    return get_object_or_404(
        ForecastQuestion.objects.select_related(
            "exercise__decision", "exercise__organisation", "exercise__owner"
        ).filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=question_id,
    )


def portfolios_for_organisation(*, user, organisation_id):
    organisation = get_object_or_404(Organisation.objects.for_user(user), id=organisation_id)
    return (
        PrioritisationPortfolio.objects.filter(organisation=organisation)
        .select_related("owner", "created_by")
        .prefetch_related(
            "criteria",
            "candidates__decision",
            "candidates__assessments__criterion",
            "candidates__assessments__assessor",
            "candidates__selection",
        )
    )


def portfolio_for_user(*, user, portfolio_id):
    return get_object_or_404(
        PrioritisationPortfolio.objects.select_related("organisation", "owner", "created_by")
        .prefetch_related(
            "criteria",
            "candidates__decision",
            "candidates__assessments__criterion",
            "candidates__assessments__assessor",
            "candidates__selection",
        )
        .filter(organisation__memberships__user=user, organisation__memberships__status="active"),
        id=portfolio_id,
    )


def candidate_for_user(*, user, candidate_id):
    return get_object_or_404(
        PortfolioCandidate.objects.select_related("portfolio__organisation", "decision").filter(
            organisation__memberships__user=user, organisation__memberships__status="active"
        ),
        id=candidate_id,
    )
