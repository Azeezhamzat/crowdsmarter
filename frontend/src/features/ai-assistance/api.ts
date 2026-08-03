import { apiRequest } from "../../lib/api";
import type { AIReview, AIReviewList, AIReviewQualityMetrics } from "../../lib/types";

export function listAIReviews(decisionId: string): Promise<AIReviewList> {
  return apiRequest<AIReviewList>(`/decisions/${decisionId}/ai-reviews/`);
}

export function getAIReviewQualityMetrics(organisationId: string): Promise<AIReviewQualityMetrics> {
  return apiRequest<AIReviewQualityMetrics>(`/organisations/${organisationId}/ai-assistance/quality/`);
}

export function requestAIReview(decisionId: string): Promise<AIReview> {
  return apiRequest<AIReview>(`/decisions/${decisionId}/ai-reviews/`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export function acknowledgeAIReview(reviewId: string, notes: string): Promise<AIReview> {
  return apiRequest<AIReview>(`/ai-reviews/${reviewId}/acknowledge/`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export function dismissAIReview(reviewId: string, reason: string): Promise<AIReview> {
  return apiRequest<AIReview>(`/ai-reviews/${reviewId}/dismiss/`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
