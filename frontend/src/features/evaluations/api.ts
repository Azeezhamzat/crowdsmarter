import { apiRequest } from "../../lib/api";
import type {
  EvaluationCriterion,
  EvaluationExercise,
  EvaluationResults,
  EvaluationRound,
  EvaluationSubmission,
  MinorityReport,
  PortfolioAssessment,
  PortfolioCandidate,
  PortfolioCriterion,
  PortfolioSelection,
  PrioritisationPortfolio,
} from "../../lib/types";

export function listEvaluations(decisionId: string): Promise<EvaluationExercise[]> {
  return apiRequest(`/decisions/${decisionId}/evaluations/`);
}

export function getEvaluation(exerciseId: string): Promise<EvaluationExercise> {
  return apiRequest(`/evaluations/${exerciseId}/`);
}

export function createEvaluation(decisionId: string, input: Record<string, unknown>): Promise<EvaluationExercise> {
  return apiRequest(`/decisions/${decisionId}/evaluations/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateEvaluation(exerciseId: string, input: Record<string, unknown>): Promise<EvaluationExercise> {
  return apiRequest(`/evaluations/${exerciseId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function addEvaluationCriterion(exerciseId: string, input: Record<string, unknown>): Promise<EvaluationCriterion> {
  return apiRequest(`/evaluations/${exerciseId}/criteria/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function createEvaluationRound(exerciseId: string, title = ""): Promise<EvaluationRound> {
  return apiRequest(`/evaluations/${exerciseId}/rounds/`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function transitionEvaluationRound(
  roundId: string,
  input: { status: "open" | "closed"; feedback_summary?: string },
): Promise<EvaluationRound> {
  return apiRequest(`/evaluation-rounds/${roundId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function saveEvaluationSubmission(
  roundId: string,
  input: Record<string, unknown>,
): Promise<EvaluationSubmission> {
  return apiRequest(`/evaluation-rounds/${roundId}/submission/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function getEvaluationResults(roundId: string): Promise<EvaluationResults> {
  return apiRequest(`/evaluation-rounds/${roundId}/results/`);
}

export function createMinorityReport(exerciseId: string, input: Record<string, unknown>): Promise<MinorityReport> {
  return apiRequest(`/evaluations/${exerciseId}/minority-reports/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listPrioritisations(organisationId: string): Promise<PrioritisationPortfolio[]> {
  return apiRequest(`/organisations/${organisationId}/prioritisations/`);
}

export function getPrioritisation(portfolioId: string): Promise<PrioritisationPortfolio> {
  return apiRequest(`/prioritisations/${portfolioId}/`);
}

export function createPrioritisation(organisationId: string, input: Record<string, unknown>): Promise<PrioritisationPortfolio> {
  return apiRequest(`/organisations/${organisationId}/prioritisations/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updatePrioritisation(portfolioId: string, input: Record<string, unknown>): Promise<PrioritisationPortfolio> {
  return apiRequest(`/prioritisations/${portfolioId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function addPortfolioCriterion(portfolioId: string, input: Record<string, unknown>): Promise<PortfolioCriterion> {
  return apiRequest(`/prioritisations/${portfolioId}/criteria/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function addPortfolioCandidate(portfolioId: string, input: Record<string, unknown>): Promise<PortfolioCandidate> {
  return apiRequest(`/prioritisations/${portfolioId}/candidates/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function savePortfolioAssessment(candidateId: string, input: Record<string, unknown>): Promise<PortfolioAssessment> {
  return apiRequest(`/prioritisation-candidates/${candidateId}/assessments/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function savePortfolioSelection(candidateId: string, input: Record<string, unknown>): Promise<PortfolioSelection> {
  return apiRequest(`/prioritisation-candidates/${candidateId}/selection/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}
