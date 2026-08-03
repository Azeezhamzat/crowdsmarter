import { apiRequest } from "../../lib/api";
import type {
  AIProviderKey,
  PlatformAdministrator,
  PlatformAuditEvent,
  PlatformConfiguration,
  PlatformContactSettings,
  PlatformDemoRequest,
  PlatformOrganisation,
  PlatformOrganisationDetail,
  PlatformOverview,
  PlatformUser,
  SupportAccessGrant,
} from "./types";

export function getPlatformOverview(): Promise<PlatformOverview> {
  return apiRequest<PlatformOverview>("/platform-admin/overview/");
}

export function listPlatformOrganisations(input: { q?: string; status?: string } = {}): Promise<PlatformOrganisation[]> {
  const query = new URLSearchParams();
  if (input.q) query.set("q", input.q);
  if (input.status) query.set("status", input.status);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<PlatformOrganisation[]>(`/platform-admin/organisations/${suffix}`);
}

export function getPlatformOrganisation(id: string): Promise<PlatformOrganisationDetail> {
  return apiRequest<PlatformOrganisationDetail>(`/platform-admin/organisations/${id}/`);
}

export function createSupportAccess(
  organisationId: string,
  input: { access_level: "read_only" | "operational"; reason: string; duration_hours: number },
): Promise<SupportAccessGrant> {
  return apiRequest<SupportAccessGrant>(`/platform-admin/organisations/${organisationId}/support-access/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function revokeSupportAccess(id: string, rationale: string): Promise<SupportAccessGrant> {
  return apiRequest<SupportAccessGrant>(`/platform-admin/support-access/${id}/revoke/`, {
    method: "POST",
    body: JSON.stringify({ rationale }),
  });
}

export function transferPlatformOwnership(
  organisationId: string,
  input: {
    target_membership_id: string;
    rationale: string;
    demote_existing_owners: boolean;
    confirmation: string;
  },
): Promise<{ detail: string; target_membership_id: string }> {
  return apiRequest(`/platform-admin/organisations/${organisationId}/ownership/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function changePlatformOrganisationState(
  organisationId: string,
  input: { action: "deactivate" | "reactivate"; rationale: string; confirmation: string },
): Promise<PlatformOrganisation> {
  return apiRequest<PlatformOrganisation>(`/platform-admin/organisations/${organisationId}/state/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function changePlatformInvitation(
  invitationId: string,
  input: { action: "resend" | "revoke"; rationale: string },
): Promise<{ detail: string; invitation_id: string; status: string; delivery_status: string | null; acceptance_url: string | null }> {
  return apiRequest(`/platform-admin/invitations/${invitationId}/action/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listPlatformUsers(input: { q?: string; state?: string } = {}): Promise<PlatformUser[]> {
  const query = new URLSearchParams();
  if (input.q) query.set("q", input.q);
  if (input.state) query.set("state", input.state);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<PlatformUser[]>(`/platform-admin/users/${suffix}`);
}

export function changePlatformUserState(
  userId: string,
  input: { is_active: boolean; rationale: string },
): Promise<PlatformUser> {
  return apiRequest<PlatformUser>(`/platform-admin/users/${userId}/state/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listPlatformAdministrators(): Promise<PlatformAdministrator[]> {
  return apiRequest<PlatformAdministrator[]>("/platform-admin/administrators/");
}

export function changePlatformAdministrator(
  userId: string,
  input: { action: "grant" | "suspend"; rationale: string },
): Promise<PlatformAdministrator> {
  return apiRequest<PlatformAdministrator>(`/platform-admin/users/${userId}/administrator/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getPlatformConfiguration(): Promise<PlatformConfiguration> {
  return apiRequest<PlatformConfiguration>("/platform-admin/configuration/");
}

export function updatePlatformConfiguration(
  input: PlatformContactSettings & { rationale: string },
): Promise<PlatformConfiguration> {
  return apiRequest<PlatformConfiguration>("/platform-admin/configuration/", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function setAIProvider(input: {
  provider_key: AIProviderKey;
  model: string;
  rationale: string;
}): Promise<PlatformConfiguration> {
  return apiRequest<PlatformConfiguration>("/platform-admin/configuration/ai-provider/", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function setAIProviderAPIKey(input: {
  api_key: string;
  rationale: string;
}): Promise<PlatformConfiguration> {
  return apiRequest<PlatformConfiguration>("/platform-admin/configuration/ai-provider/api-key/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function clearAIProviderAPIKey(input: { rationale: string }): Promise<PlatformConfiguration> {
  return apiRequest<PlatformConfiguration>("/platform-admin/configuration/ai-provider/api-key/", {
    method: "DELETE",
    body: JSON.stringify(input),
  });
}

export function listPlatformDemoRequests(input: { q?: string; status?: string } = {}): Promise<PlatformDemoRequest[]> {
  const query = new URLSearchParams();
  if (input.q) query.set("q", input.q);
  if (input.status) query.set("status", input.status);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<PlatformDemoRequest[]>(`/platform-admin/demo-requests/${suffix}`);
}

export function updatePlatformDemoRequestStatus(
  id: string,
  input: { status: PlatformDemoRequest["status"]; rationale: string },
): Promise<PlatformDemoRequest> {
  return apiRequest<PlatformDemoRequest>(`/platform-admin/demo-requests/${id}/status/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listPlatformAudit(input: { q?: string; action?: string } = {}): Promise<PlatformAuditEvent[]> {
  const query = new URLSearchParams();
  if (input.q) query.set("q", input.q);
  if (input.action) query.set("action", input.action);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<PlatformAuditEvent[]>(`/platform-admin/audit/${suffix}`);
}
