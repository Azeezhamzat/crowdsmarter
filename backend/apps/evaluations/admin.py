from django.contrib import admin

from .models import (EvaluationCriterion, EvaluationExercise, EvaluationResponse, EvaluationRound, EvaluationSubmission, MinorityReport, PortfolioAssessment, PortfolioCandidate, PortfolioCriterion, PortfolioSelection, PrioritisationPortfolio)

for model in [EvaluationExercise,EvaluationCriterion,EvaluationRound,EvaluationSubmission,EvaluationResponse,MinorityReport,PrioritisationPortfolio,PortfolioCriterion,PortfolioCandidate,PortfolioAssessment,PortfolioSelection]:
    admin.site.register(model)
