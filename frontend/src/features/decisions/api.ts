import { apiRequest } from "../../lib/api";
import type {
  Decision,
  DecisionOverview,
  DecisionStatus,
  DecisionSummary,
  DecisionTemplate,
  DecisionTransition,
  DecisionUrgency,
} from "../../lib/types";

export function listDecisions(workspaceId: string): Promise<DecisionSummary[]> {
  return apiRequest<DecisionSummary[]>(`/workspaces/${workspaceId}/decisions/`);
}

export function getDecision(decisionId: string): Promise<Decision> {
  return apiRequest<Decision>(`/decisions/${decisionId}/`);
}

export function getDecisionOverview(decisionId: string): Promise<DecisionOverview> {
  return apiRequest<DecisionOverview>(`/decisions/${decisionId}/overview/`);
}

export function listDecisionTemplates(): Promise<DecisionTemplate[]> {
  return apiRequest<DecisionTemplate[]>("/decision-templates/");
}

export type DecisionCreateInput = {
  template_key: string;
  method_version_id?: string | null;
  title: string;
  decision_question: string;
  purpose: string;
  context: string;
  scope: string;
  contribution_guidance: string;
  urgency: DecisionUrgency;
  target_decision_date: string | null;
  contribution_deadline: string | null;
  owner_id?: string;
};

export function createDecision(
  workspaceId: string,
  input: DecisionCreateInput,
): Promise<Decision> {
  return apiRequest<Decision>(`/workspaces/${workspaceId}/decisions/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export type DecisionUpdateInput = {
  title?: string;
  decision_question?: string;
  purpose?: string;
  context?: string;
  scope?: string;
  contribution_guidance?: string;
  urgency?: DecisionUrgency;
  target_decision_date?: string | null;
  contribution_deadline?: string | null;
  owner_id?: string;
};

export function updateDecision(
  decisionId: string,
  input: DecisionUpdateInput,
): Promise<Decision> {
  return apiRequest<Decision>(`/decisions/${decisionId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function listDecisionTransitions(
  decisionId: string,
): Promise<DecisionTransition[]> {
  return apiRequest<DecisionTransition[]>(`/decisions/${decisionId}/transitions/`);
}

export function transitionDecision(
  decisionId: string,
  input: { expected_status: DecisionStatus; rationale: string },
): Promise<DecisionTransition> {
  return apiRequest<DecisionTransition>(`/decisions/${decisionId}/transitions/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}
