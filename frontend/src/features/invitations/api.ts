import { apiRequest, ensureCsrfCookie } from "../../lib/api";
import type {
  InvitationAcceptance,
  InvitationDispatch,
  InvitationPublicDetails,
  OrganisationInvitation,
  OrganisationRole,
} from "../../lib/types";

export function listInvitations(organisationId: string): Promise<OrganisationInvitation[]> {
  return apiRequest<OrganisationInvitation[]>(
    `/organisations/${organisationId}/invitations/`,
  );
}

export function createInvitation(
  organisationId: string,
  input: { email: string; role: OrganisationRole },
): Promise<InvitationDispatch> {
  return apiRequest<InvitationDispatch>(
    `/organisations/${organisationId}/invitations/`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export function resendInvitation(invitationId: string): Promise<InvitationDispatch> {
  return apiRequest<InvitationDispatch>(
    `/organisation-invitations/${invitationId}/resend/`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function revokeInvitation(
  invitationId: string,
): Promise<OrganisationInvitation> {
  return apiRequest<OrganisationInvitation>(
    `/organisation-invitations/${invitationId}/revoke/`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function getInvitation(rawToken: string): Promise<InvitationPublicDetails> {
  return apiRequest<InvitationPublicDetails>("/invitations/accept/", {
    headers: { "X-Invitation-Token": rawToken },
  });
}

export async function acceptInvitation(
  rawToken: string,
  input: {
    first_name?: string;
    last_name?: string;
    password?: string;
    password_confirm?: string;
  },
): Promise<InvitationAcceptance> {
  await ensureCsrfCookie();
  return apiRequest<InvitationAcceptance>("/invitations/accept/", {
    method: "POST",
    headers: { "X-Invitation-Token": rawToken },
    body: JSON.stringify(input),
  });
}
