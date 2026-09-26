from django.contrib import admin

from .models import (
    EvaluationCriterion,
    EvaluationExercise,
    EvaluationResponse,
    EvaluationRound,
    EvaluationSubmission,
    Forecast,
    ForecastQuestion,
    MinorityReport,
    PortfolioAssessment,
    PortfolioCandidate,
    PortfolioCriterion,
    PortfolioSelection,
    PrioritisationPortfolio,
)

for model in [
    EvaluationExercise,
    EvaluationCriterion,
    EvaluationRound,
    EvaluationSubmission,
    EvaluationResponse,
    MinorityReport,
    PrioritisationPortfolio,
    PortfolioCriterion,
    PortfolioCandidate,
    PortfolioAssessment,
    PortfolioSelection,
    ForecastQuestion,
    Forecast,
]:
    admin.site.register(model)
