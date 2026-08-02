import { apiRequest } from "../../lib/api";
import type { DecisionMethod, DecisionMethodUsage } from "../../lib/types";

export function listDecisionMethods(organisationId: string): Promise<DecisionMethod[]> {
  return apiRequest<DecisionMethod[]>(`/organisations/${organisationId}/decision-methods/`);
}

export function createDecisionMethod(organisationId: string, input: Record<string, unknown>): Promise<DecisionMethod> {
  return apiRequest<DecisionMethod>(`/organisations/${organisationId}/decision-methods/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function cloneBuiltInMethod(organisationId: string, input: { builtin_key: string; name?: string }): Promise<DecisionMethod> {
  return apiRequest<DecisionMethod>(`/organisations/${organisationId}/decision-methods/clone/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function createMethodVersion(methodId: string) {
  return apiRequest(`/decision-methods/${methodId}/versions/`, { method: "POST", body: "{}" });
}

export function updateMethodVersion(versionId: string, input: Record<string, unknown>) {
  return apiRequest(`/decision-method-versions/${versionId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function approveMethodVersion(versionId: string) {
  return apiRequest(`/decision-method-versions/${versionId}/approve/`, { method: "POST", body: "{}" });
}

export function retireDecisionMethod(methodId: string, reason: string) {
  return apiRequest(`/decision-methods/${methodId}/retire/`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export function listDecisionMethodUsage(organisationId: string): Promise<DecisionMethodUsage[]> {
  return apiRequest<DecisionMethodUsage[]>(`/organisations/${organisationId}/decision-method-usage/`);
}
