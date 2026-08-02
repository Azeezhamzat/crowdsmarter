import { apiRequest } from "../../lib/api";
import type {
  DecisionReview,
  Lesson,
  LessonCategory,
  OutcomeAssessment,
} from "../../lib/types";

export function getDecisionReview(decisionId: string): Promise<{ review: DecisionReview | null }> {
  return apiRequest<{ review: DecisionReview | null }>(`/decisions/${decisionId}/review/`);
}

export type CommitmentInput = {
  expected_status: string;
  implementation_owner_id: string;
  commitment_statement: string;
  success_measures: string;
  review_due_date: string;
  rationale: string;
};

export function recordCommitment(decisionId: string, input: CommitmentInput): Promise<DecisionReview> {
  return apiRequest<DecisionReview>(`/decisions/${decisionId}/commitment/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function startImplementation(
  decisionId: string,
  input: { expected_status: string; implementation_plan: string; rationale: string },
): Promise<DecisionReview> {
  return apiRequest<DecisionReview>(`/decisions/${decisionId}/implementation/start/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function openOutcomeReview(
  decisionId: string,
  input: { expected_status: string; implementation_summary: string; rationale: string },
): Promise<DecisionReview> {
  return apiRequest<DecisionReview>(`/decisions/${decisionId}/outcome-review/open/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function completeOutcomeReview(
  decisionId: string,
  input: {
    expected_status: string;
    outcome_summary: string;
    outcome_assessment: OutcomeAssessment;
    review_evidence: string;
    unintended_consequences?: string;
    rationale: string;
  },
): Promise<DecisionReview> {
  return apiRequest<DecisionReview>(`/decisions/${decisionId}/outcome-review/complete/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listLessons(decisionId: string): Promise<Lesson[]> {
  return apiRequest<Lesson[]>(`/decisions/${decisionId}/lessons/`);
}

export type LessonInput = {
  title: string;
  insight: string;
  category: LessonCategory;
  applicability: string;
  recommended_change?: string;
};

export function createLesson(decisionId: string, input: LessonInput): Promise<Lesson> {
  return apiRequest<Lesson>(`/decisions/${decisionId}/lessons/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function retireLesson(lessonId: string): Promise<Lesson> {
  return apiRequest<Lesson>(`/lessons/${lessonId}/`, { method: "DELETE" });
}

export function archiveDecision(
  decisionId: string,
  input: { expected_status: string; rationale: string },
): Promise<void> {
  return apiRequest<void>(`/decisions/${decisionId}/archive/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function changeImplementationOwner(
  decisionId: string,
  implementationOwnerId: string,
): Promise<DecisionReview> {
  return apiRequest<DecisionReview>(`/decisions/${decisionId}/review/`, {
    method: "PATCH",
    body: JSON.stringify({ implementation_owner_id: implementationOwnerId }),
  });
}
