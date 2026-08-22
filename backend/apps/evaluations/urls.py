from django.urls import path

from .views import (EvaluationCriterionCreateView, EvaluationExerciseDetailView, EvaluationExerciseListCreateView, EvaluationResultsView, EvaluationRoundCreateView, EvaluationRoundTransitionView, EvaluationScoringOptionsView, EvaluationSubmissionView, MinorityReportCreateView, PortfolioAssessmentView, PortfolioCandidateCreateView, PortfolioCriterionCreateView, PortfolioSelectionView, PrioritisationPortfolioDetailView, PrioritisationPortfolioListCreateView)

app_name="evaluations"
urlpatterns=[
    path("decisions/<uuid:decision_id>/evaluations/",EvaluationExerciseListCreateView.as_view(),name="decision-evaluations"),
    path("evaluations/<uuid:exercise_id>/",EvaluationExerciseDetailView.as_view(),name="evaluation-detail"),
    path("evaluations/<uuid:exercise_id>/criteria/",EvaluationCriterionCreateView.as_view(),name="evaluation-criteria"),
    path("evaluations/<uuid:exercise_id>/scoring-options/",EvaluationScoringOptionsView.as_view(),name="evaluation-scoring-options"),
    path("evaluations/<uuid:exercise_id>/rounds/",EvaluationRoundCreateView.as_view(),name="evaluation-rounds"),
    path("evaluation-rounds/<uuid:round_id>/",EvaluationRoundTransitionView.as_view(),name="evaluation-round-transition"),
    path("evaluation-rounds/<uuid:round_id>/submission/",EvaluationSubmissionView.as_view(),name="evaluation-submission"),
    path("evaluation-rounds/<uuid:round_id>/results/",EvaluationResultsView.as_view(),name="evaluation-results"),
    path("evaluations/<uuid:exercise_id>/minority-reports/",MinorityReportCreateView.as_view(),name="evaluation-minority-reports"),
    path("organisations/<uuid:organisation_id>/prioritisations/",PrioritisationPortfolioListCreateView.as_view(),name="prioritisation-portfolios"),
    path("prioritisations/<uuid:portfolio_id>/",PrioritisationPortfolioDetailView.as_view(),name="prioritisation-detail"),
    path("prioritisations/<uuid:portfolio_id>/criteria/",PortfolioCriterionCreateView.as_view(),name="prioritisation-criteria"),
    path("prioritisations/<uuid:portfolio_id>/candidates/",PortfolioCandidateCreateView.as_view(),name="prioritisation-candidates"),
    path("prioritisation-candidates/<uuid:candidate_id>/assessments/",PortfolioAssessmentView.as_view(),name="prioritisation-assessment"),
    path("prioritisation-candidates/<uuid:candidate_id>/selection/",PortfolioSelectionView.as_view(),name="prioritisation-selection"),
]
