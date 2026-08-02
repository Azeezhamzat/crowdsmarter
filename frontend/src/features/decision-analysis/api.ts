import { apiRequest } from "../../lib/api";
import type { DecisionAnalysisIssue, DecisionAnalysisWorkspace, DecisionQualityReview, ExecutiveDecisionSummary } from "../../lib/types";

export function getDecisionAnalysis(decisionId: string): Promise<DecisionAnalysisWorkspace> {
  return apiRequest<DecisionAnalysisWorkspace>(`/decisions/${decisionId}/analysis/`);
}
export function listDecisionIssues(decisionId: string): Promise<DecisionAnalysisIssue[]> {
  return apiRequest<DecisionAnalysisIssue[]>(`/decisions/${decisionId}/analysis/issues/`);
}
export function createDecisionIssue(decisionId: string, input: Record<string, unknown>): Promise<DecisionAnalysisIssue> {
  return apiRequest<DecisionAnalysisIssue>(`/decisions/${decisionId}/analysis/issues/`, { method: "POST", body: JSON.stringify(input) });
}
export function updateDecisionIssue(issueId: string, input: Record<string, unknown>): Promise<DecisionAnalysisIssue> {
  return apiRequest<DecisionAnalysisIssue>(`/decision-analysis/issues/${issueId}/`, { method: "PATCH", body: JSON.stringify(input) });
}
export function listQualityReviews(decisionId: string): Promise<DecisionQualityReview[]> {
  return apiRequest<DecisionQualityReview[]>(`/decisions/${decisionId}/analysis/quality-reviews/`);
}
export function createQualityReview(decisionId: string, input: Record<string, unknown>): Promise<DecisionQualityReview> {
  return apiRequest<DecisionQualityReview>(`/decisions/${decisionId}/analysis/quality-reviews/`, { method: "POST", body: JSON.stringify(input) });
}
export function updateQualityReview(reviewId: string, input: Record<string, unknown>): Promise<DecisionQualityReview> {
  return apiRequest<DecisionQualityReview>(`/decision-analysis/quality-reviews/${reviewId}/`, { method: "PATCH", body: JSON.stringify(input) });
}
export function listExecutiveSummaries(decisionId: string): Promise<ExecutiveDecisionSummary[]> {
  return apiRequest<ExecutiveDecisionSummary[]>(`/decisions/${decisionId}/analysis/executive-summaries/`);
}
export function createExecutiveSummary(decisionId: string, input: Record<string, unknown>): Promise<ExecutiveDecisionSummary> {
  return apiRequest<ExecutiveDecisionSummary>(`/decisions/${decisionId}/analysis/executive-summaries/`, { method: "POST", body: JSON.stringify(input) });
}
export function updateExecutiveSummary(summaryId: string, input: Record<string, unknown>): Promise<ExecutiveDecisionSummary> {
  return apiRequest<ExecutiveDecisionSummary>(`/decision-analysis/executive-summaries/${summaryId}/`, { method: "PATCH", body: JSON.stringify(input) });
}
