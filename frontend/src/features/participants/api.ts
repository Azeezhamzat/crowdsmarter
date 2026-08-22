import { apiRequest } from "../../lib/api";
import type { ConflictOfInterest, ConflictOfInterestScope, Participant, ParticipantRole } from "../../lib/types";

export function listParticipants(decisionId: string): Promise<Participant[]> {
  return apiRequest<Participant[]>(`/decisions/${decisionId}/participants/`);
}

export function addParticipant(
  decisionId: string,
  input: { email: string; role: Exclude<ParticipantRole, "decision_owner"> },
): Promise<Participant> {
  return apiRequest<Participant>(`/decisions/${decisionId}/participants/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function changeParticipantRole(
  participantId: string,
  role: Exclude<ParticipantRole, "decision_owner">,
): Promise<Participant> {
  return apiRequest<Participant>(`/participants/${participantId}/`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function removeParticipant(participantId: string): Promise<void> {
  return apiRequest<void>(`/participants/${participantId}/`, {
    method: "DELETE",
  });
}

export function listConflicts(participantId: string): Promise<ConflictOfInterest[]> {
  return apiRequest<ConflictOfInterest[]>(`/participants/${participantId}/conflicts/`);
}

export function declareConflict(
  participantId: string,
  input: { scope: ConflictOfInterestScope; option_id?: string | null; reason?: string },
): Promise<ConflictOfInterest> {
  return apiRequest<ConflictOfInterest>(`/participants/${participantId}/conflicts/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function withdrawConflict(conflictId: string): Promise<ConflictOfInterest> {
  return apiRequest<ConflictOfInterest>(`/conflicts/${conflictId}/withdraw/`, {
    method: "POST",
  });
}
