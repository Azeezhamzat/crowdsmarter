import { apiRequest } from "../../lib/api";
import type { OrganisationSubscription, Plan } from "../../lib/types";

export function listPlans(): Promise<Plan[]> {
  return apiRequest<Plan[]>("/plans/");
}

export function getOrganisationSubscription(organisationId: string): Promise<OrganisationSubscription> {
  return apiRequest<OrganisationSubscription>(`/organisations/${organisationId}/subscription/`);
}

export function changeOrganisationPlan(
  organisationId: string,
  input: { plan_key: string },
): Promise<OrganisationSubscription> {
  return apiRequest<OrganisationSubscription>(`/organisations/${organisationId}/subscription/plan/`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function setOrganisationBillingContact(
  organisationId: string,
  input: { user_id: string | null },
): Promise<OrganisationSubscription> {
  return apiRequest<OrganisationSubscription>(
    `/organisations/${organisationId}/subscription/billing-contact/`,
    { method: "POST", body: JSON.stringify(input) },
  );
}
