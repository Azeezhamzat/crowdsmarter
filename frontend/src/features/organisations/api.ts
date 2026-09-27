import { apiRequest } from "../../lib/api";
import type {
  Membership,
  MembershipEvent,
  Organisation,
  OrganisationDeletionRequest,
  OrganisationRole,
} from "../../lib/types";

export function listOrganisations(): Promise<Organisation[]> {
  return apiRequest<Organisation[]>("/organisations/");
}

export function getOrganisation(id: string): Promise<Organisation> {
  return apiRequest<Organisation>(`/organisations/${id}/`);
}

export function createOrganisation(input: {
  name: string;
  slug: string;
}): Promise<Organisation> {
  return apiRequest<Organisation>("/organisations/", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listMemberships(organisationId: string): Promise<Membership[]> {
  return apiRequest<Membership[]>(`/organisations/${organisationId}/memberships/`);
}


export function changeMembershipRole(
  membershipId: string,
  role: OrganisationRole,
): Promise<Membership> {
  return apiRequest<Membership>(`/organisations/memberships/${membershipId}/`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function removeMembership(membershipId: string): Promise<void> {
  return apiRequest<void>(`/organisations/memberships/${membershipId}/`, {
    method: "DELETE",
  });
}

export function updateOrganisationAdministration(
  organisationId: string,
  input: Record<string, unknown>,
): Promise<Organisation> {
  return apiRequest<Organisation>(`/organisations/${organisationId}/administration/`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function listMembershipHistory(organisationId: string) {
  return apiRequest<MembershipEvent[]>(`/organisations/${organisationId}/membership-history/`);
}

export function transferOrganisationOwnership(
  organisationId: string,
  input: { target_membership_id: string; rationale: string },
) {
  return apiRequest(`/organisations/${organisationId}/transfer-ownership/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function deactivateOrganisation(
  organisationId: string,
  input: { confirmation: string; reason: string },
): Promise<Organisation> {
  return apiRequest<Organisation>(`/organisations/${organisationId}/deactivate/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function reactivateOrganisation(organisationId: string, rationale: string): Promise<Organisation> {
  return apiRequest<Organisation>(`/organisations/${organisationId}/reactivate/`, {
    method: "POST",
    body: JSON.stringify({ rationale }),
  });
}

export function listOrganisationDeletionRequests(organisationId: string) {
  return apiRequest<OrganisationDeletionRequest[]>(`/organisations/${organisationId}/deletion-requests/`);
}

export function requestOrganisationDeletion(
  organisationId: string,
  input: { confirmation: string; reason: string },
) {
  return apiRequest<OrganisationDeletionRequest>(`/organisations/${organisationId}/deletion-requests/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function cancelOrganisationDeletion(requestId: string, rationale: string) {
  return apiRequest(`/organisations/deletion-requests/${requestId}/cancel/`, {
    method: "POST",
    body: JSON.stringify({ rationale }),
  });
}
