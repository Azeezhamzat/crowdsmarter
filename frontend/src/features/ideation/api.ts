import { apiRequest, ensureCsrfCookie } from "../../lib/api";
import type { OpenSessionOrganiser, OpenSessionPublic, OpenSessionSummary } from "../../lib/types";

const PARTICIPANT_TOKEN_HEADER = "X-Participant-Token";

function participantStorageKey(publicSlug: string): string {
  return `crowdsmarter:open-session:${publicSlug}:participant-token`;
}

export function getStoredParticipantToken(publicSlug: string): string | null {
  return window.localStorage.getItem(participantStorageKey(publicSlug));
}

export function storeParticipantToken(publicSlug: string, token: string): void {
  window.localStorage.setItem(participantStorageKey(publicSlug), token);
}

function participantHeaders(publicSlug: string): HeadersInit | undefined {
  const token = getStoredParticipantToken(publicSlug);
  return token ? { [PARTICIPANT_TOKEN_HEADER]: token } : undefined;
}

export function getPublicSession(publicSlug: string): Promise<OpenSessionPublic> {
  return apiRequest<OpenSessionPublic>(`/public/sessions/${publicSlug}/`, {
    headers: participantHeaders(publicSlug),
  });
}

export async function joinSession(
  publicSlug: string,
  input: { name: string; email: string },
): Promise<{ participant_token: string; name: string }> {
  await ensureCsrfCookie();
  const result = await apiRequest<{ participant_token: string; name: string }>(
    `/public/sessions/${publicSlug}/join/`,
    { method: "POST", body: JSON.stringify(input) },
  );
  storeParticipantToken(publicSlug, result.participant_token);
  return result;
}

export async function submitIdea(
  publicSlug: string,
  input: { title: string; description?: string },
): Promise<OpenSessionPublic> {
  await ensureCsrfCookie();
  return apiRequest<OpenSessionPublic>(`/public/sessions/${publicSlug}/ideas/`, {
    method: "POST",
    body: JSON.stringify(input),
    headers: participantHeaders(publicSlug),
  });
}

export async function voteIdea(publicSlug: string, ideaId: string): Promise<OpenSessionPublic> {
  await ensureCsrfCookie();
  return apiRequest<OpenSessionPublic>(`/public/sessions/${publicSlug}/ideas/${ideaId}/vote/`, {
    method: "POST",
    headers: participantHeaders(publicSlug),
  });
}

export async function removeVote(publicSlug: string, ideaId: string): Promise<OpenSessionPublic> {
  await ensureCsrfCookie();
  return apiRequest<OpenSessionPublic>(`/public/sessions/${publicSlug}/ideas/${ideaId}/vote/`, {
    method: "DELETE",
    headers: participantHeaders(publicSlug),
  });
}

export function listOrganisationSessions(organisationId: string): Promise<OpenSessionSummary[]> {
  return apiRequest<OpenSessionSummary[]>(`/organisations/${organisationId}/sessions/`);
}

export function createOrganisationSession(
  organisationId: string,
  input: {
    title: string;
    prompt: string;
    description?: string;
    decision_id?: string | null;
    voting_enabled?: boolean;
    submission_deadline?: string | null;
  },
): Promise<OpenSessionSummary> {
  return apiRequest<OpenSessionSummary>(`/organisations/${organisationId}/sessions/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getOrganiserSession(sessionId: string): Promise<OpenSessionOrganiser> {
  return apiRequest<OpenSessionOrganiser>(`/sessions/${sessionId}/`);
}

export function setSessionState(sessionId: string, action: "open" | "close"): Promise<OpenSessionOrganiser> {
  return apiRequest<OpenSessionOrganiser>(`/sessions/${sessionId}/state/`, {
    method: "POST",
    body: JSON.stringify({ action }),
  });
}

export function shortlistIdea(
  sessionId: string,
  ideaId: string,
  shortlisted: boolean,
): Promise<OpenSessionOrganiser> {
  return apiRequest<OpenSessionOrganiser>(`/sessions/${sessionId}/ideas/${ideaId}/shortlist/`, {
    method: "POST",
    body: JSON.stringify({ shortlisted }),
  });
}

export function promoteIdea(
  sessionId: string,
  ideaId: string,
  decisionId: string,
): Promise<OpenSessionOrganiser> {
  return apiRequest<OpenSessionOrganiser>(`/sessions/${sessionId}/ideas/${ideaId}/promote/`, {
    method: "POST",
    body: JSON.stringify({ decision_id: decisionId }),
  });
}
