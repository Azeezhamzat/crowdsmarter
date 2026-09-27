import { apiRequest, downloadApiFile } from "../../lib/api";
import type {
  ContributionPreference,
  ContributionRequest,
  FacilitationAgendaItem,
  FacilitationAuthorityResponse,
  FacilitationRecord,
  DecisionContributionWorkspace,
  FacilitationQualityReview,
  FacilitationSession,
  PersonalContributionWork,
} from "../../lib/types";

export function getDecisionContributions(decisionId: string): Promise<DecisionContributionWorkspace> {
  return apiRequest(`/decisions/${decisionId}/contribution-requests/`);
}

export function createContributionRequest(decisionId: string, input: Record<string, unknown>): Promise<ContributionRequest> {
  return apiRequest(`/decisions/${decisionId}/contribution-requests/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateContributionRequest(
  requestId: string,
  input: Record<string, unknown>,
): Promise<ContributionRequest> {
  return apiRequest(`/contribution-requests/${requestId}/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function contributionAction(requestId: string, action: string, reason = ""): Promise<ContributionRequest> {
  return apiRequest(`/contribution-requests/${requestId}/actions/`, {
    method: "POST",
    body: JSON.stringify({ action, reason }),
  });
}

export function saveContributionDraft(requestId: string, body: string, references: string): Promise<{ id: string }> {
  return apiRequest(`/contribution-requests/${requestId}/draft/`, {
    method: "PUT",
    body: JSON.stringify({ body, references }),
  });
}

export function submitContribution(requestId: string, body: string, references: string): Promise<{ id: string }> {
  return apiRequest(`/contribution-requests/${requestId}/submit/`, {
    method: "POST",
    body: JSON.stringify({ body, references }),
  });
}

export function reviewContribution(requestId: string, outcome: string, note: string): Promise<unknown> {
  return apiRequest(`/contribution-requests/${requestId}/review/`, {
    method: "POST",
    body: JSON.stringify({ outcome, note }),
  });
}

export function listFacilitationSessions(decisionId: string): Promise<FacilitationSession[]> {
  return apiRequest(`/decisions/${decisionId}/facilitation-sessions/`);
}

export function createFacilitationSession(decisionId: string, input: Record<string, unknown>): Promise<FacilitationSession> {
  return apiRequest(`/decisions/${decisionId}/facilitation-sessions/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateFacilitationSessionStatus(sessionId: string, status: string): Promise<FacilitationSession> {
  return apiRequest(`/facilitation-sessions/${sessionId}/status/`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export function createFacilitationAgendaItem(
  sessionId: string,
  input: Record<string, unknown>,
): Promise<FacilitationAgendaItem> {
  return apiRequest(`/facilitation-sessions/${sessionId}/agenda-items/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function facilitationAgendaItemAction(
  itemId: string,
  action: "start" | "complete" | "skip" | "reset",
): Promise<FacilitationAgendaItem> {
  return apiRequest(`/facilitation-agenda-items/${itemId}/actions/`, {
    method: "POST",
    body: JSON.stringify({ action }),
  });
}

export function createFacilitationRecord(
  sessionId: string,
  input: Record<string, unknown>,
): Promise<FacilitationRecord> {
  return apiRequest(`/facilitation-sessions/${sessionId}/records/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function saveFacilitationAuthorityResponse(
  sessionId: string,
  input: Record<string, unknown>,
): Promise<FacilitationAuthorityResponse> {
  return apiRequest(`/facilitation-sessions/${sessionId}/authority-response/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function saveFacilitationQualityReview(
  sessionId: string,
  input: Record<string, unknown>,
): Promise<FacilitationQualityReview> {
  return apiRequest(`/facilitation-sessions/${sessionId}/quality-review/`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function downloadFacilitationReport(sessionId: string): Promise<string> {
  return downloadApiFile(
    `/facilitation-sessions/${sessionId}/report/`,
    "text/html",
    "crowdsmarter-facilitation-report.html",
  );
}

export function getPersonalContributions(): Promise<PersonalContributionWork> {
  return apiRequest("/contributions/my-work/");
}

export function getContributionPreference(organisationId: string): Promise<ContributionPreference> {
  return apiRequest(`/organisations/${organisationId}/contribution-preferences/`);
}

export function updateContributionPreference(
  organisationId: string,
  input: Pick<ContributionPreference, "digest_cadence" | "email_enabled" | "due_reminders_enabled" | "reminder_days_before">,
): Promise<ContributionPreference> {
  return apiRequest(`/organisations/${organisationId}/contribution-preferences/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function updateSessionAttendance(participantId: string, attendance: string): Promise<unknown> {
  return apiRequest(`/facilitation-participants/${participantId}/attendance/`, {
    method: "POST",
    body: JSON.stringify({ attendance }),
  });
}
